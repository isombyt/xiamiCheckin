import urllib
import urllib2
import cookielib
import StrCookieJar
import re
import time
from datetime import datetime

uid_re="/web/friends/id/([0-9]*)\""

def get_info(email,password):
    info={}
    cookie=StrCookieJar.StrCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    urllib2.install_opener(opener)
    #login
    login_url = 'http://www.xiami.com/web/login'
    login_data = urllib.urlencode({'email':email, 'password':password, 'LoginButton':'\xe7\x99\xbb\xe9\x99\x86',})
    login_headers = {'Referer':'http://www.xiami.com/web/login', 'User-Agent':'Opera/9.60',}
    login_request = urllib2.Request(login_url, login_data, login_headers)
    #login_url='http://www.xiami.com/web'
    #login_request = urllib2.Request(login_url)
    urllib2.urlopen(login_request)
    profile_url="http://www.xiami.com/web/profile"
    profile_request = urllib2.Request(profile_url)
    profile_response=urllib2.urlopen(profile_request).read()
    info['id']=re.findall(uid_re,profile_response)[0]
    info['cookie']=cookie.dump()
    return info
    
def checkin(user):
    cookie=StrCookieJar.StrCookieJar(user.cookie)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    urllib2.install_opener(opener)

    checkin_url="http://www.xiami.com/web/checkin/id/"+user.uid
    checkin_headers = {'Referer':'http://www.xiami.com/web/', 'User-Agent':'Opera/9.99',}
    #checkin_url="http://www.xiami.com/web"
    checkin_request = urllib2.Request(checkin_url, None, checkin_headers)
    checkin_response=urllib2.urlopen(checkin_request).read()
    checkin_pattern = re.compile(r'<a class="check_in" href="(.*?)">')
    checkin_result = checkin_pattern.search(checkin_response)
    if not checkin_result:
        pattern = re.compile(r'<div class="idh">\xe5\xb7\xb2\xe8\xbf\x9e\xe7\xbb\xad\xe7\xad\xbe\xe5\x88\xb0(\d+)\xe5\xa4\xa9</div>')
        result = pattern.search(checkin_response)
        if result:
            return result.group(1),checkin_response
        else :
            return None,checkin_response
    checkin_url = 'http://www.xiami.com' + checkin_result.group(1)
    checkin_headers = {'Referer':'http://www.xiami.com/web', 'User-Agent':'BH_Toolchain0.5',}
    checkin_request = urllib2.Request(checkin_url, None, checkin_headers)
    checkin_response = urllib2.urlopen(checkin_request).read()
    pattern = re.compile(r'<div class="idh">\xe5\xb7\xb2\xe8\xbf\x9e\xe7\xbb\xad\xe7\xad\xbe\xe5\x88\xb0(\d+)\xe5\xa4\xa9</div>')
    result = pattern.search(checkin_response)
    if result:
        return result.group(1),checkin_response
    else :
        return None,checkin_response



from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import urlfetch
from google.appengine.ext import db


class user(db.Model):
    email = db.StringProperty()
    uid = db.StringProperty()
    cookie = db.BlobProperty()
    last = db.DateTimeProperty()
    days = db.IntegerProperty()
    errcount = db.IntegerProperty()

class MainHandler(webapp.RequestHandler):
    
    def post(self):
        email=self.request.get('email')
        password=self.request.get('password')
        try:
            info=get_info(email,password)
            newuser=user.get_or_insert(info['id'], uid=info['id'])
            date=datetime.fromtimestamp(0)
            newuser.last=datetime.fromtimestamp(0)
            newuser.cookie=info['cookie']
            newuser.email=email
            newuser.errcount=0
            newuser.put()
            self.response.out.write("email:%s</br>"%email)
            self.response.out.write("uid:%s</br>"%info['id'])
            self.response.out.write("cookie:%s</br>"%info['cookie'])
            self.response.out.write('\xe7\x99\xbb\xe8\xae\xb0\xe6\x88\x90\xe5\x8a\x9f\xef\xbc\x8c\xe8\xaf\xb7\xe5\x85\xb3\xe9\x97\xad\xe9\xa1\xb5\xe9\x9d\xa2')
        except:
            self.response.out.write('\xe5\x8f\x91\xe7\x94\x9f\xe9\x94\x99\xe8\xaf\xaf\xef\xbc\x8c\xe8\xaf\xb7\xe9\x87\x8d\xe8\xaf\x95')

    def get(self):
        self.response.out.write(file("reg.html").read())

class CronWorkHandler(webapp.RequestHandler):
    
    def get(self):
        users=db.GqlQuery("select * from user where last!=NULL ORDER BY last ASC limit 1")
        for auser in users:
            try:
                if auser.last<datetime.fromtimestamp(time.mktime(time.gmtime())+28800).replace(hour=0,minute=0,second=0):
                    self.response.out.write(auser.uid)
                    result,respon=checkin(auser)
                    if result:
                        auser.days=int(result)
                        self.response.out.write(result)
                    else:
                        self.response.out.write(respon)
                        return 
                    auser.last=datetime.fromtimestamp(time.mktime(time.gmtime())+27000).replace(hour=0,minute=0,second=0)
                    auser.errcount=0
                    auser.put()
                else:
                    self.response.out.write("All have been check in .")
                return
            except:
                auser.errcount+=1
                auser.last=auser.last.replace(minute=auser.last.minute+10)
                auser.put()

    def post(self):
        pass

class CheckHandler(webapp.RequestHandler):

    def get(self):
        email=self.request.get('email')
        if email:
            users=db.GqlQuery("select * from user where email=:1",email)
            if users==None:
                self.response.out.write("No record")
                return 
            for auser in users:
                self.response.out.write("email:%s</br>"%auser.email)
                self.response.out.write("uid:%s</br>"%auser.uid)
                self.response.out.write("days:%s</br>"%auser.days)

    def post(self):
        return 

class UpdateHandler(webapp.RequestHandler):

    def get(self):
        alluser=db.GqlQuery("select * from user")
        for auser in alluser:
            auser.last=datetime.fromtimestamp(0)
            auser.put()
            self.response.out.write(auser.uid+':'+str(auser.last)+'</br>')

    def post(self):
        pass


app = webapp.WSGIApplication([('/', MainHandler),
                              ('/CronJob',CronWorkHandler),
                              ('/check',CheckHandler),
                              ('/update',UpdateHandler)],
                            debug=True)

def main():
    util.run_wsgi_app(app)


if __name__=="__main__":
    main()

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi

from database_setup import Brewery, BeerName, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///beer.db')
text_factory = str
Base.metadata.bind = engine
# Creates the session
DBSession = sessionmaker(bind=engine)
session = DBSession()


class webserverHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            if self.path.endswith("/breweries/new"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<html><body>"
                output += "<h1> Make a New Brewery</h1>"
                output += "<form method='POST' enctype='multipart/form-data' action='/breweries/new'>"
                output += "<input name= 'newBreweryName' type='text' place = 'New Brewery Name' >"
                output += "<input type= 'submit' value='Create'>"
                output += "</html></body>"
                self.wfile.write(output)
                return

            if self.path.endswith("/edit"):
                breweryIDPath = self.path.split("/")[2]
                myBreweryQuery = session.query(Brewery).filter_by(id=breweryIDPath).one()
                if myBreweryQuery:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    output = "<html><body>"
                    output += "<h1>"
                    output += myBreweryQuery.name
                    output += "</h1>"
                    output += "<form method='POST' enctype='multipart/form-data' action='/breweries/%s/edit' >" % breweryIDPath
                    output += "<input name= 'newBreweryName' type='text' placeholder = '%s' >" % myBreweryQuery.name
                    output += "<input type= 'submit' value='Rename'>"
                    output += "</form>"
                    output += "</body></html>"

                    self.wfile.write(output)

            if self.path.endswith("/delete"):

                breweryIDPath = self.path.split("/")[2]
                myBreweryQuery = session.query(Brewery).filter_by(id = breweryIDPath).one()
                if myBreweryQuery != [] :
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    output = ""
                    output = "<html><body>"
                    output = "<h1>Are you sure you to delete %s?" % myBreweryQuery.name
                    output += "<form method='POST' enctype='multipart/form-data' action='/breweries/%s/delete' >" % breweryIDPath
                    output += "<input type= 'submit' value='Delete'>"
                    output += "</form>"
                    output += "</body></html>"
                    self.wfile.write(output)

            if self.path.endswith("/breweries"):
                breweries = session.query(Brewery).all()
                output = ""
                output += "<a href = '/breweries/new' > Make a New Brewery </a></br></br>"
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output += "<html><body>"
                for brewery in breweries:
                    output += brewery.name
                    output += "</br>"
                    output += "<a href =' /breweries/%s/edit' >Edit </a> " % brewery.id
                    output += "</br>"
                    output += "<a href ='/breweries/%s/delete'>Delete </a>" % brewery.id
                    output += "</br>"
                output += "</body></html>"
                self.wfile.write(output)
                # print output
                return

        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        try:
            if self.path.endswith("/delete"):
                breweryIDPath = self.path.split("/")[2]

                myBreweryQuery = session.query(Brewery).filter_by(id = breweryIDPath).one()

                if myBreweryQuery !=[] :
                    session.delete(myBreweryQuery)
                    session.commit()
                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Location', '/breweries')
                    self.end_headers()

            if self.path.endswith("/edit"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                messagecontent = fields.get('newBreweryName')
                breweryIDPath = self.path.split("/")[2]

                myBreweryQuery = session.query(
                    Brewery).filter_by(id=breweryIDPath).one()
                if myBreweryQuery != []:
                    myBreweryQuery.name = messagecontent[0]
                    session.add(myBreweryQuery)
                    session.commit()
                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Location', '/breweries')
                    self.end_headers()

            if self.path.endswith("/breweries/new"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('newBreweryName')

                    newBrewery = Brewery(name=messagecontent[0])
                    session.add(newBrewery)
                    session.commit()

                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Location', '/breweries')
                    self.send_header()

        #   self.send_response(301)
        #   self.end_headers()

        #   ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        #   if ctype == 'multipart/form-data':
        #       fields=cgi.parse_multipart(self.rfile, pdict)
        #       messagecontent = fields.get('message')

        #   output = ""
        #   output += "<html><body>"
        #   output += " <h2> Okay, how about this: </h2>"
        #   output += "<h1> %s </h1>" % messagecontent[0]

        #   output += "<form method='POST' enctype='multipart/form-data' action='/hello'><h2>What would you like me to say?</h2><input name='message' type='text' ><input type='submit' value='Submit'></form>"
        #   output += "</body></html>"
        #   self.wfile.write(output)
        #   print output
        except:
            pass


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), webserverHandler)
        print "Web server running on port %s" % port
        server.serve_forever()
    except KeyboardInterrupt:
        print "^C entered, stopping web server...."
        server.socket.close()

if __name__ == '__main__':
    main()

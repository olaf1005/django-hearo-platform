import socketserver
import http.server
import re

PORT = 9090


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):

        if None is not re.search("/api/square/*", self.path):
            num = float(self.path.split("/")[-1])
            print(self.path.split("/"))
            # This URL will trigger our sample function and send what it returns back to the browser
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(str(num * num))  # call sample function here
            return
        if None is not re.search("/api/mult/*", self.path):
            num1 = float(self.path.split("/")[-1])
            num2 = float(self.path.split("/")[-2])
            # This URL will trigger our sample function and send what it returns back to the browser
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(str(num1 * num2))  # call sample function here
            return
        else:
            # serve files, and directory listings by following self.path from
            # current working directory
            http.server.SimpleHTTPRequestHandler.do_GET(self)


httpd = socketserver.ThreadingTCPServer(("", PORT), CustomHandler)

print("serving at port {}".format(PORT))
httpd.serve_forever()

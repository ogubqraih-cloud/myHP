#!/bin/sh
cd /Users/oguramasashi/Desktop/myHP
exec /usr/bin/ruby -run -e httpd -- -p 3000 .

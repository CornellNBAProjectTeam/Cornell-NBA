# Cornell-NBA-
This is the repository for our state of the art NBA match prediction project

# How to Install:
* First make sure that your `pip` and `virtualenv` versions are up to date. If you don't have `virtualenv`, type `pip install virtualenv`.

* Next, go into the project directory and type `virtualenv venv` to create a virtual environment in a folder called venv.

* Type `source venv/bin/activate` to use the virtual environment instead of your local machine.

* Then type `pip install -r requirements.txt` to install package dependencies.

* Finally, to exit the local environment, type `deactivate`.

Make sure to always be in the virtual environment when running the program or have the dependencies installed locally.

# NGINX and uWSGI
worker_processes 1;

events {

    worker_connections 1024;

}

http {

    sendfile on;

    gzip              on;
    gzip_http_version 1.0;
    gzip_proxied      any;
    gzip_min_length   500;
    gzip_disable      "MSIE [1-6]\.";
    gzip_types        text/plain text/xml text/css
                      text/comma-separated-values
                      text/javascript
                      application/x-javascript
                      application/atom+xml;

    # Configuration containing list of application servers
    upstream uwsgicluster {

        server 127.0.0.1:8080;
        # server 127.0.0.1:8081;
        # ..
        # .

    }

    # Configuration for Nginx
    server {

        # Running port
        listen 80;

        # Proxying connections to application servers
        location / {

            include            uwsgi_params;
            uwsgi_pass         uwsgicluster;

            proxy_redirect     off;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Host $server_name;

        }
    }
}

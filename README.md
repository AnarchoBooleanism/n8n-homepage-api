# n8n-homepage-api
API server that provides n8n statistics to use for Homepage by querying its SQL server

This supports at least Python 3.12, and uses FastAPI, SQLModel, and psycopg2. Currently, this server only supports the PostgreSQL backend, but support for other backends are planned for the future.

To start the server (assuming all requirements are installed), run this command in the root directory of the repository:
```bash
fastapi run
```

Alternatively, you can run it in a Docker container with this command:
```bash
docker run -p 8000:8000 \
  --env POSTGRES_USER="MYSQLUSER" \
  --env POSTGRES_PASSWORD="MYSQLPASSWORD" \
  --env POSTGRES_HOST="localhost" \
  --env POSTGRES_DB="n8n" \
  ghcr.io/anarchobooleanism/n8n-homepage-api:latest
```

Ensure that the SQL server that you intend to connect to is operational before you start.

For an example on using this with Docker Compose, check out this [example configuration](compose.yaml).

## Setting up with a Docker container

The preferred choice for using the image associated with this project is with [Docker Compose](compose.yaml). This is a quick example of what the configuration could look like:
```yaml
n8n-homepage-api: # Our service over here!
  image: ghcr.io/anarchobooleanism/n8n-homepage-api:latest
  container_name: n8n-postgres
  ports:
    - "8000:8000"
  environment:
    POSTGRES_USER: "postgres"
    POSTGRES_PASSWORD: "testpassword"
    POSTGRES_HOST: n8n-postgres
    POSTGRES_PORT: "5432"
    POSTGRES_DB: n8n
```

This creates a service which exposes the endpoint for our API server on port 8000 on the host. Note that, to connect to the PostgreSQL server, we will need to provide connection details to the server in our environment variables: particularly, we will need to set `POSTGRES_USER` with our username, `POSTGRES_PASSWORD` with our password, `POSTGRES_HOST` with the hostname/IP address of the server, `POSTGRES_PORT` with the port number of the server, and `POSTGRES_DB` with the name of the database that we will use.

Furthermore, this service will need to have access to the PostgreSQL server, whether it is in a container or not. If it is in a container, make sure that this service and the PostgreSQL service either share a Docker network (if a Compose file has both services but no specific networks listed, there will be a default bridge network generated for you) or through the `links` attribute in each service. This is what it would look like:
```yaml
services:
  postgres:
    image: postgres:16
    container_name: n8n-postgres
    ports:
      - "5432:5432"
    ... (omitted for brevity)
    networks:
      - n8n_internal
    ...
  
  n8n-homepage-api: # Our service over here!
    image: ghcr.io/anarchobooleanism/n8n-homepage-api:latest
    container_name: n8n-postgres
    depends_on:
      postgres:
        condition: service_healthy
    ...
    networks:
      - n8n_internal
    ...

networks:
  n8n_internal: # This is the name of our network
```

In this configuration, there is a Docker network named `n8n_internal`, which both services are linked to: this allows their containers to directly connect with each other with their container names.

To deploy our setup, simply run `docker compose up -d` in the same directory as our Compose file. If we have any extra environment variables that we want to pass to Docker that exist in a `.env` file, simply run this command: `docker compose --env-file .env up -d`

### Note on reverse proxies

If you are running the API server behind a reverse proxy, there is no need to expose the server's port directly; just make sure that the reverse proxy can communicate with the container directly (via a shared network) and direct traffic to it, like this, for Traefik:
```yaml
n8n-homepage-api: # Our service over here!
  image: ghcr.io/anarchobooleanism/n8n-homepage-api:latest
  container_name: n8n-postgres
  ... (omitted for brevity)
  labels:
    traefik.enable: "true"
    traefik.http.routers.n8n-homepage-api.rule: Host(`n8n-api.example.com`)
    traefik.http.routers.n8n-homepage-api.tls: "true"
    traefik.http.routers.n8n-homepage-api.entrypoints: websecure
    traefik.http.routers.n8n-homepage-api.tls.certresolver: letsencrypt
    traefik.http.routers.n8n-homepage-api.tls.domains[0].main: n8n-api.example.com
    ...
    traefik.http.routers.n8n-homepage-api.service: n8n-homepage-api-svc
    traefik.http.services.n8n-homepage-api-svc.loadbalancer.server.port: "8000" # FastAPI listens to 8000 by default
  ...
  networks:
    - n8n_internal
    - web_bridge # This is the network that Traefik is on and can communicate through
  ...
```

In this example, the service is added to a network that Traefik is also on, `web_bridge`; this network can have any name, and for the sake of this guide, it will be created externally to our n8n setup. For Traefik, various labels are applied to the service which allow Traefik to know what endpoint to redirect traffic from (via the `n8n-homepage-api` router), and how to redirect traffic to the service (via the `n8n-homepage-api-svc` Traefik service that goes to the container's port 8000). For other reverse proxies, simply make sure that the desired endpoint is connected to the container on the right port.

However, you may not want to dedicate an entire subdomain to the API server, and instead, have it served on a specific path on an existing domain. To do this, in your reverse proxy, connect a specific subpath to the API server. This is what it would look like in Traefik, using labels:
```yaml
n8n-homepage-api: # Our service over here!
  image: ghcr.io/anarchobooleanism/n8n-homepage-api:latest
  container_name: n8n-postgres
  ... (omitted for brevity)
  labels:
    traefik.enable: "true"
    traefik.http.routers.n8n-homepage-api.rule: Host(`n8n.example.com`) && Path(`/api/homepage-custom`)
    traefik.http.routers.n8n-homepage-api.tls: "true"
    traefik.http.routers.n8n-homepage-api.entrypoints: websecure
    traefik.http.routers.n8n-homepage-api.tls.certresolver: letsencrypt
    traefik.http.routers.n8n-homepage-api.tls.domains[0].main: n8n.example.com
    traefik.http.middlewares.n8n-homepage-api-stripprefix.stripprefix.prefixes: /api/homepage-custom # Since our API listens at "/", we need to strip our path prefix out for it to work properly
    traefik.http.routers.n8n-homepage-api.middlewares: n8n-homepage-api-stripprefix
    traefik.http.routers.n8n-homepage-api.service: n8n-homepage-api-svc
    traefik.http.services.n8n-homepage-api-svc.loadbalancer.server.port: "8000" # FastAPI listens to 8000 by default
  environment:
    ...
    ROOT_PATH_PREFIX: "/api/homepage-custom" # Since Traefik serves the API at a custom path, we need to pass this to FastAPI so it can be aware of it
  ...
``` 

In this example, the router for `n8n-homepage-api` is configured for traffic going to both the host `n8n.example.com` and the path `/api/homepage-custom`. Furthermore, there is a piece of middleware that removes the `/api/homepage-custom` path prefix before sending requests to the API server, so that it only sees requests to the specific endpoints that it expects (e.g. the root endpoint `/`). This works fine for regular use, but when reading the live documentation, this may lead to confusion as it will display URLs that are missing these prefixes, and will not directly to their locations as prescribed by the reverse proxy; to fix this, we have the `ROOT_PATH_PREFIX` environment variable set to our path prefix so that FastAPI can add it back when generating its documentation.

## Setting up outside of a container

If you prefer to run this server in a native environment, outside of a container, this is also possible, but we will need to make sure that the operating system's environment has everything needed to run the server. This guide is oriented towards using a virtual environment with venv, but you are welcome to use your distribution's native Python module packages in this process too, or pipx.

First of all, we will need to have Python installed to our system, as well as pip and venv support. For example, with Ubuntu's native package manager, apt, we would run something like this: `sudo apt install python3 python3-pip python3-venv`

Once Python is completely installed, we can now clone this Git repository to any desired directory: `git clone https://github.com/AnarchoBooleanism/n8n-homepage-api.git`

With the repository cloned, make the root directory of the repository your working directory, and create your virtual environment with venv, going to the subdirectory `venv`: `python -m venv venv`

With the virtual environment created, activate it in your terminal, adding the necessary paths to your PATH variable: `source venv/bin/activate`
> If using Windows, simply run `venv/bin/Activate.ps1` in PowerShell.

Now that the virtual environment is completely loaded in our PATH, we can install all of the necessary pip packages to this virtual environment: `pip install -r requirements.txt`

Finally, with all the packages installed to the virtual environment, and everything ready for deployment, we can start the FastAPI server: `fastapi run`
> *NOTE:* Every time that you run this command between sessions, make sure the virtual environment is activated first: `source venv/bin/activate`

All environment variables related to PostgreSQL are required to be provided when starting the FastAPI server, like this:
```bash
POSTGRES_USER="postgres" POSTGRES_PASSWORD="mypassword" \
POSTGRES_HOST="localhost" POSTGRES_PORT="5432" POSTGRES_DB="n8n" \
fastapi run
```

If you want to change the host address and port used by FastAPI, use the arguments `--port` and `--host` like this:
```bash
fastapi --port 8000 --host 0.0.0.0 run
```

If you want to change the root path prefix to provide to FastAPI, use the argument `--root-path` like this:
```bash
fastapi --root-path "/my-custom-path/api" run
```

If you want to change the list of forwarded allowed IP addresses to provide to FastAPI, use the argument `--forwarded-allow-ips` like this:
```bash
fastapi --forwarded-allow-ips="192.168.0.1,192.168.0.2" run
```

### Running as a service
If you prefer that the API server start on system startup, then you can create a dedicated service or scheduled task that loads the virtual environment in the PATH and then starts the FastAPI server.

This is an example of what it would look like as a systemd service that starts a script:
```ini
[Unit]
Description=n8n-homepage-api
After=network.target

[Service]
Type=simple
User=myuser
EnvironmentFile=/path/to/my/.env
ExecStart="/PATH/TO/MY/VENV/bin/fastapi --host 0.0.0.0 --port 8000 run"
Environment="PATH=/PATH/TO/MY/VENV/bin:/usr/local/bin:/usr/bin:/bin"
WorkingDirectory=/path/to/my/repo
Restart=always
RestartSec=1

[Install]
WantedBy=multi-user.target
```

This service starts the API server once networking is working, setting the environment and working directory so that, when the `fastapi` file is started, it knows where to look for the project files and has access to the proper binaries in the right PATH; it also is given the environment variables from the `.env` file so that it can connect to the PostgreSQL server. Importantly, note that all references to files and directories on the system are done with absolute paths, and not relative paths, as systemd will not work with relative paths; it assumes nothing, and we will have to give it all of the context that it requires.

To get the service up and running, save the file as `/etc/systemd/system/n8n-homepage-api.service`, run `systemd daemon-reload` as root, and then run `systemd enable --now n8n-homepage-api` as root. To check on the status of the new service, run `systemd status n8n-homepage-api`.

If everything works correctly, then you should now have a systemd service that will automatically start the API server on system startup, with no manual intervention.

## List of environment variables
- `POSTGRES_USER` - If using PostgreSQL, the username to connect to the SQL server with. Defaults to `postgres`.
- `POSTGRES_PASSWORD` - If using PostgreSQL, the password to connect to the SQL server with.
- `POSTGRES_HOST` (optional) - If using PostgreSQL, the hostname or IP address of the SQL server to connect to. Defaults to `localhost`.
- `POSTGRES_PORT` (optional) - If using PostgreSQL, the port number of the SQL server to connect to. Defaults to `5432`.
- `POSTGRES_DB` (optional) - If using PostgreSQL, the name of the database to use. Defaults to `n8n`.
- `FASTAPI_HOST` (optional) - The host/IP address for FastAPI to bind to. Defaults to `0.0.0.0` (all available interfaces).
- `FASTAPI_PORT` (optional) - The port number for FastAPI to listen to. Defaults to `8000`.
- `ROOT_PATH_PREFIX` (optional) - If the root path through which the API is being served (such as through a reverse proxy) is different to what FastAPI expects (typically the root), the prefix of the root prefix to know to check for. Defaults to `/` (the root path).
- `FORWARDED_ALLOW_IPS` (optional) - A comma-separated list of IP address to trust with proxy headers (e.g. `X-Forwarded-For`). Defaults to `*` (trust everything).

## Intended behavior

When a GET request is sent to the root endpoint, the server should respond with the number of workflows that exist within n8n (the count of unique IDs in the `workflow_entities` table), and a number of executions that exist within n8n (the count of unique IDs in the `execution_entities` table), respectively in the `workflows` and `executions` attributes, like this:
```json
{
    "workflows": 2,
    "executions": 10
}
```
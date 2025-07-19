FROM postgres:17

# Copy initialization scripts
COPY init/*.sql /docker-entrypoint-initdb.d/

# Set default environment variables
ENV POSTGRES_DB=inmobiliario_db
ENV TZ=Europe/Madrid
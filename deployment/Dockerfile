#This is the first stage, it is named requirements-stage.
FROM python:3.10.12-slim as requirements-stage

# Set the working directory in the container
WORKDIR /tmp

# Install Poetry and the export plugin in this Docker stage.
RUN pip install poetry && poetry self add poetry-plugin-export

# Copy the pyproject.toml and poetry.lock files to the /tmp directory.
COPY ./pyproject.toml ./poetry.lock* /tmp/

# Generate the requirements.txt file.
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes



# This is the final stage, anything here will be preserved in the final container image.
FROM python:3.10.12-slim

# Set the current working directory to /code.
WORKDIR /code

# Copy the requirements.txt file to the /code directory.
# This file only lives in the previous Docker stage, that's why we use --from-requirements-stage to copy it.
COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt

# Update the package lists for upgrades for packages and install gcc and libpq-dev
RUN apt-get update && apt-get install -y gcc libpq-dev

# Install the package dependencies in the generated requirements.txt file.
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./alembic /code/alembic
COPY ./alembic.ini /code
COPY ./datapipeline /code/datapipeline
COPY ./scripts /code/scripts
# COPY ./.env /code/.env


# Copy the pipeline script into the Docker image
RUN chmod +x /code/scripts/pipeline.sh


ENTRYPOINT ["/code/scripts/pipeline.sh"]

# Run the datapipeline command, telling it to use the app object imported from
CMD ["python", "-m", "datapipeline.main"]

# Stage 1 - Build stuf_zds_payments environment
FROM python:3.12-slim-bullseye AS stuf-zds-payments-build

WORKDIR /app

RUN pip install pip -U
COPY . /app
RUN pip install .


# Stage 2 - Build the production image with the stuf_zds_payments
FROM openformulieren/open-forms:latest AS production-build

WORKDIR /app

# Copy the dependencies of the stuf_zds_payments
COPY --from=stuf-zds-payments-build /usr/local/lib/python3.12 /usr/local/lib/python3.12

# Add stuf_zds_payments code to the image
COPY --chown=maykin:root ./stuf_zds_payments /app/src/stuf_zds_payments

USER maykin
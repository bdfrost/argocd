FROM golang:1.23-alpine AS builder

RUN apk add --no-cache git

WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download
COPY main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -o /build/instagram-monitor .

FROM alpine:3.23
RUN apk add --no-cache ca-certificates
RUN adduser -D appuser
USER appuser
COPY --from=builder --chown=appuser /build/instagram-monitor /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/instagram-monitor"]

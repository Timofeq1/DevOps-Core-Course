FROM golang:1.21-alpine AS builder

WORKDIR /app

RUN adduser -D -g '' appuser

COPY go.mod .
COPY main.go .

RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o app main.go

FROM scratch

WORKDIR /app

COPY --from=builder /etc/passwd /etc/passwd

COPY --from=builder /app/app /app/app

EXPOSE 8080

USER appuser

ENTRYPOINT ["/app/app"]

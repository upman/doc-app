This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Local dev
- Setup .env files
```
cp .env.example .env
cp backend/.env.example backend/.env
## Add your anthropic key in the file above
```

- Setup and run backend frontend:

```bash
make setup
make install

yarn dev # run frontend
make dev # run backend
```

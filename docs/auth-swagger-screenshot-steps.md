# Swagger authentication screenshot

1. Start the stack and open `http://localhost:8000/docs`.
2. Run `POST /auth/login` and copy the returned `access_token`.
3. Click **Authorize** at the top of Swagger UI.
4. Paste the token only (Swagger adds the `Bearer` prefix).
5. Execute `GET /protected/profile` and confirm status `200`.
6. Capture a screenshot showing the Authorize control, protected-route lock icon, and successful profile response.
7. Save it as `docs/auth-swagger.png`.

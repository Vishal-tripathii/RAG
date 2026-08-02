function LoginForm() {
  return (
    <form className="auth-form">
      <h2>Log in</h2>

      <label htmlFor="login-email">Email</label>
      <input id="login-email" name="email" type="email" />

      <label htmlFor="login-password">Password</label>
      <input id="login-password" name="password" type="password" />

      <button type="submit">Log in</button>
    </form>
  )
}

export default LoginForm

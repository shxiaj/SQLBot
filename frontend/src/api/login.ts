import { request } from '@/utils/request'

const simpleEncrypt = (text: string): string => {
  try {
    return btoa(unescape(encodeURIComponent(text)))
  } catch {
    return text
  }
}

const simpleDecrypt = (text: string): string => {
  try {
    return decodeURIComponent(escape(atob(text)))
  } catch {
    return text
  }
}

export const AuthApi = {
  login: (credentials: { username: string; password: string }) => {
    const entryCredentials = {
      username: simpleEncrypt(credentials.username),
      password: simpleEncrypt(credentials.password),
    }
    return request.post<{
      data: any
      token: string
    }>('/login/access-token', entryCredentials, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
  },
  logout: (data: any) => request.post('/login/logout', data),
  info: () => request.get('/user/info'),
}

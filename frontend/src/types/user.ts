export type UserPermission = 'student' | 'manager' | 'dev'

export interface User {
  user_id: string
  email: string
  nick_name: string | null
  permission: UserPermission
  is_verified: boolean
}

export type UserPermission = 'student' | 'manager' | 'dev'

export interface User {
  user_id: string
  email: string
  nick_name: string | null
  permission: UserPermission
  is_verified: boolean
}

export interface UserBrief {
  user_id: string
  email: string
  nick_name: string | null
}

import { redirect } from 'next/navigation'

export default function SettingsPage() {
  // デフォルトでアカウント設定にリダイレクト
  redirect('/settings/account')
}
import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  validateStatus: () => true,
})

export async function fetchDays() {
  const res = await client.get('/days/')
  if (res.status >= 400) {
    return { ok: false, errors: res.data.errors }
  }
  return { ok: true, data: res.data }
}

export async function fetchDay(date) {
  const res = await client.get(`/days/${date}/`)
  if (res.status >= 400) {
    return { ok: false, errors: res.data.errors }
  }
  return { ok: true, data: res.data }
}

export async function createTrip(body) {
  const res = await client.post('/trips/', body)
  if (res.status >= 400) {
    return { ok: false, errors: res.data.errors || { detail: 'Не удалось сохранить поездку' } }
  }
  return { ok: true, data: res.data }
}

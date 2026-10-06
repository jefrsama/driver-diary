<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { createTrip, fetchDay, fetchDays } from './services/api'

const selectedDate = ref('2026-10-01')
const dates = ref([])
const day = ref(null)
const loading = ref(false)
const loadError = ref('')
const submitting = ref(false)
const formError = ref('')
const notice = ref('')
const skipWatch = ref(true)
let requestSeq = 0

const form = reactive({
  id: newTripId(),
  start: '2026-10-01T08:00',
  end: '2026-10-01T08:30',
  amount: '',
  payment: 'card',
  commission: '',
})

const summary = computed(() => day.value?.summary || null)
const trips = computed(() => day.value?.trips || [])

function newTripId() {
  return `t${Date.now().toString(36)}`
}

function cents(value) {
  const text = String(value).trim().replace(',', '.')
  const negative = text.startsWith('-')
  const [whole, frac = ''] = text.replace('-', '').split('.')
  const total = Number(whole || 0) * 100 + Number((frac + '00').slice(0, 2))
  return negative ? -total : total
}

function formatFromCents(total) {
  const sign = total < 0 ? '−' : ''
  const abs = Math.abs(total)
  const grouped = new Intl.NumberFormat('ru-RU').format(Math.floor(abs / 100))
  return `${sign}${grouped},${String(abs % 100).padStart(2, '0')} ₸`
}

function formatMoney(value) {
  return formatFromCents(cents(value))
}

function formatTime(iso) {
  return new Intl.DateTimeFormat('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Almaty',
  }).format(new Date(iso))
}

function formatDateLabel(isoDate) {
  const [year, month, dayNumber] = isoDate.split('-').map(Number)
  return new Intl.DateTimeFormat('ru-RU', {
    weekday: 'short',
    day: 'numeric',
    month: 'long',
  }).format(new Date(year, month - 1, dayNumber))
}

function durationMinutes(start, end) {
  return Math.round((new Date(end) - new Date(start)) / 60000)
}

function tripCountLabel(count) {
  const abs = Math.abs(count) % 100
  const last = abs % 10
  if (abs > 10 && abs < 20) return `${count} поездок`
  if (last === 1) return `${count} поездка`
  if (last >= 2 && last <= 4) return `${count} поездки`
  return `${count} поездок`
}

function paymentLabel(payment) {
  if (payment === 'cash') return 'Наличные'
  if (payment === 'card') return 'Карта'
  return payment
}

function errorText(errors) {
  if (!errors) return 'Не удалось выполнить запрос'
  return Object.values(errors).join('. ')
}

function toApiDateTime(value) {
  if (value.length === 16) return `${value}:00+05:00`
  return `${value}+05:00`
}

function shiftDate(isoDate, delta) {
  const [year, month, dayNumber] = isoDate.split('-').map(Number)
  const next = new Date(year, month - 1, dayNumber)
  next.setDate(next.getDate() + delta)
  const monthText = String(next.getMonth() + 1).padStart(2, '0')
  const dayText = String(next.getDate()).padStart(2, '0')
  return `${next.getFullYear()}-${monthText}-${dayText}`
}

async function loadDay() {
  const current = ++requestSeq
  loading.value = true
  loadError.value = ''
  const res = await fetchDay(selectedDate.value)
  if (current !== requestSeq) return
  loading.value = false
  if (!res.ok) {
    loadError.value = errorText(res.errors)
    day.value = null
    return
  }
  day.value = res.data
}

async function refreshDates() {
  const res = await fetchDays()
  if (!res.ok) return
  dates.value = res.data.dates
}

function resetForm() {
  form.id = newTripId()
  form.start = `${selectedDate.value}T08:00`
  form.end = `${selectedDate.value}T08:30`
  form.amount = ''
  form.payment = 'card'
  form.commission = ''
}

async function onSubmit() {
  if (submitting.value) return
  submitting.value = true
  formError.value = ''
  notice.value = ''
  const res = await createTrip({
    id: form.id.trim(),
    start: toApiDateTime(form.start),
    end: toApiDateTime(form.end),
    amount: form.amount,
    payment: form.payment,
    commission: form.commission,
  })
  submitting.value = false
  if (!res.ok) {
    formError.value = errorText(res.errors)
    return
  }
  notice.value = res.data.created
    ? 'Поездка добавлена'
    : 'Такая поездка уже была в дневнике'
  const tripDay = res.data.trip.start.slice(0, 10)
  await refreshDates()
  if (selectedDate.value !== tripDay) {
    selectedDate.value = tripDay
  } else {
    await loadDay()
  }
  resetForm()
}

function selectDate(value) {
  selectedDate.value = value
}

watch(selectedDate, () => {
  if (skipWatch.value) return
  notice.value = ''
  loadDay()
})

onMounted(async () => {
  await refreshDates()
  await loadDay()
  skipWatch.value = false
})
</script>

<template>
  <div class="page">
    <header class="top">
      <div>
        <p class="eyebrow">Смена водителя</p>
        <h1>Дневник поездок</h1>
      </div>
      <p class="tz">Время — Астана, UTC+5</p>
    </header>

    <section class="daybar">
      <button type="button" class="nav" @click="selectDate(shiftDate(selectedDate, -1))">
        Предыдущий день
      </button>
      <label class="date-field">
        <span>День</span>
        <input v-model="selectedDate" type="date" />
      </label>
      <button type="button" class="nav" @click="selectDate(shiftDate(selectedDate, 1))">
        Следующий день
      </button>
      <strong class="day-label">{{ formatDateLabel(selectedDate) }}</strong>
    </section>

    <div v-if="dates.length" class="chips">
      <button
        v-for="item in dates"
        :key="item"
        type="button"
        class="chip"
        :class="{ 'chip--on': item === selectedDate }"
        @click="selectDate(item)"
      >
        {{ formatDateLabel(item) }}
      </button>
    </div>

    <p v-if="loading" class="status">Загрузка дня…</p>
    <p v-if="loadError" class="banner banner--bad">{{ loadError }}</p>

    <div class="layout">
      <main>
        <section v-if="summary" class="cards">
          <article>
            <span>Поездки</span>
            <strong>{{ summary.trip_count }}</strong>
          </article>
          <article>
            <span>Выручка</span>
            <strong>{{ formatMoney(summary.revenue) }}</strong>
          </article>
          <article>
            <span>Комиссия</span>
            <strong>{{ formatMoney(summary.commission) }}</strong>
          </article>
          <article class="cards__net">
            <span>На руки</span>
            <strong>{{ formatMoney(summary.net) }}</strong>
          </article>
        </section>

        <section v-if="summary" class="split">
          <article>
            <span>Наличные</span>
            <strong>{{ formatMoney(summary.cash.revenue) }}</strong>
            <small>{{ tripCountLabel(summary.cash.trip_count) }}</small>
          </article>
          <article>
            <span>Карта</span>
            <strong>{{ formatMoney(summary.card.revenue) }}</strong>
            <small>{{ tripCountLabel(summary.card.trip_count) }}</small>
          </article>
        </section>

        <section class="sheet">
          <h2>Поездки за день</h2>
          <p v-if="!loading && trips.length === 0" class="empty">За этот день поездок нет</p>
          <table v-if="trips.length">
            <thead>
              <tr>
                <th>Номер</th>
                <th>Начало</th>
                <th>Окончание</th>
                <th>Минуты</th>
                <th>Оплата</th>
                <th class="num">Сумма</th>
                <th class="num">Комиссия</th>
                <th class="num">На руки</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in trips" :key="item.id">
                <td>{{ item.id }}</td>
                <td class="center">{{ formatTime(item.start) }}</td>
                <td class="center">{{ formatTime(item.end) }}</td>
                <td class="center">{{ durationMinutes(item.start, item.end) }}</td>
                <td>
                  <span class="pay" :class="`pay--${item.payment}`">{{ paymentLabel(item.payment) }}</span>
                </td>
                <td class="num">{{ formatMoney(item.amount) }}</td>
                <td class="num">{{ formatMoney(item.commission) }}</td>
                <td class="num">{{ formatFromCents(cents(item.amount) - cents(item.commission)) }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </main>

      <aside class="form-card">
        <h2>Новая поездка</h2>
        <form @submit.prevent="onSubmit">
          <label>
            Номер
            <input v-model="form.id" required maxlength="64" />
          </label>
          <label>
            Начало
            <input v-model="form.start" type="datetime-local" required />
          </label>
          <label>
            Окончание
            <input v-model="form.end" type="datetime-local" required />
          </label>
          <label>
            Сумма
            <input v-model="form.amount" inputmode="decimal" required />
          </label>
          <label>
            Оплата
            <select v-model="form.payment">
              <option value="card">Карта</option>
              <option value="cash">Наличные</option>
            </select>
          </label>
          <label>
            Комиссия
            <input v-model="form.commission" inputmode="decimal" required />
          </label>
          <p v-if="formError" class="banner banner--bad">{{ formError }}</p>
          <p v-if="notice" class="banner banner--ok">{{ notice }}</p>
          <button type="submit" class="submit" :disabled="submitting">
            {{ submitting ? 'Сохранение…' : 'Добавить поездку' }}
          </button>
        </form>
      </aside>
    </div>
  </div>
</template>

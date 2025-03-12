import { configureStore } from '@reduxjs/toolkit'
import orderReducer from './slices/orders.ts'

export default configureStore({
  reducer: {
    orders: orderReducer,


  },
})
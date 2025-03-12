import { createSlice } from '@reduxjs/toolkit'

// redux state
export const orderSlice = createSlice({
  name: 'orders',
  initialState: {
    value: [], 
    foodItems: null,
    drinkItems: null,
    customItems: null,
    finalOrder: null,
    nextAudioNew: null,
    totalCost: null,
  },
  reducers: {
    addPrompt: (state, action) => {
      state.value.unshift(action.payload)
    },
    clearPrompts: (state) => {
      state.value = []
    },
    updatePrompt: (state, action) => {
      const index = state.value.findIndex(item => item.prompt === action.payload.prompt);

      // If the prompt is found, update the fulfillmentText
      if (index !== -1) {
        state.value[index].fulfillmentText = action.payload.fulfillmentText;
      }
    },
    setFoodItems: (state, action) => {
      state.foodItems = action.payload; 
    },
    setDrinkItems: (state, action) => {
      state.drinkItems = action.payload; 
    },
    setTotalCost: (state, action) => {
      state.totalCost = action.payload; 
    },

    setCustomizationItems: (state, action) => {
      state.customItems = action.payload;
    },
    setFinalOrder: (state, action) => {
      state.finalOrder = action.payload; 
    },
    setNextAudioNew: (state, action) => {
      state.nextAudioNew = action.payload; 
    },
  },
})

// Action creators are generated for each case reducer function
export const { addPrompt, setTotalCost, setNextAudioNew, clearPrompts, setDrinkItems, setFoodItems, setCustomizationItems , updatePrompt, setFinalOrder} = orderSlice.actions

export default orderSlice.reducer
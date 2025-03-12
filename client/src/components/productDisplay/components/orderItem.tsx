import React from "react"
import { OrderItemWrapper, OrderPrompt } from "./orderItem.style.tsx";
import speechLogo from '../../../speechMcd.png'
import serverLogo from '../../../server.png'

type OrderItemProps = {
    order: any; 
}
export const OrderItem = ({ order } : OrderItemProps) => {
        return (
        <OrderItemWrapper>
                {order.fulfillmentText ? 
                 <OrderPrompt>
                        <img src={serverLogo} alt='mcd-logo-text' width={30} height={30} /> 
                        <p>{order.fulfillmentText}</p>
                </OrderPrompt>  
                : 
                <OrderPrompt>
                        <img src={serverLogo} alt='mcd-logo-text' width={30} height={30} /> 
                        <p>Processing request...</p>
                </OrderPrompt>  
                }
                <OrderPrompt>
                        <img src={speechLogo} alt='mcd-logo-text' width={30} height={30} />
                        <p>{order.prompt}</p>
                </OrderPrompt>
        </OrderItemWrapper>
        )
}
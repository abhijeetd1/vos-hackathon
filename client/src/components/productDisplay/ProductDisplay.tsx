import React, { useEffect, useState } from "react"
import { OrderItems, ProductDisplayWrapper } from "./ProductDisplay.style.tsx"
import { useSelector } from "react-redux";
import { OrderItem } from "./components/orderItem.tsx";
import { Loader } from "../orderSummary/OrderSummary.style.tsx";

type ProductDisplayProps = {
    transcript: string; 
    recording: boolean;
    waitingForTranscript?: boolean; 
}

const ProductDisplay = () => {
    const orders = useSelector((state : any) => state.orders.value)

    return (

        <ProductDisplayWrapper>
                <OrderItems>
                    {orders.map((order) => {
                        return <OrderItem order={order} />
                    })}
                </OrderItems>
        </ProductDisplayWrapper>
    )

}

export default ProductDisplay
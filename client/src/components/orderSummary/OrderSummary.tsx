import React from "react";
import { Customization, ItemAndPrice, ItemsWrapper, OrderDetails, OrderItemWrapper, OrderSummaryWrapper, OrderTotal, Title } from "./OrderSummary.style.tsx";
import { useSelector } from "react-redux";
import burgerLogo from '../../burger.jpg'; 
import drinkLogo from '../../drink.jpg'; 
import friesLogo from '../../fries.jpg'; 
import defaultLogo from '../../default.png'; 


const OrderSummary = () => {

    const orderItems = useSelector((state : any) => state.orders.foodItems)
    const totalCost = useSelector((state : any) => state.orders.totalCost)

    const drinkNames = ['soda', 'drink', 'coffee', 'pop', 'water', 'fountain drink'];
    const burgerNames = ['hamburger', 'cheeseburger', 'burger', 'big mac'];
    const friesNames = ['fries', 'french fries'];


    const getImage = (productName: string) => {
        if (burgerNames.includes(productName.toLowerCase())) {
            return burgerLogo
        }
        if (friesNames.includes(productName.toLowerCase())) {
            return friesLogo
        }
        if (drinkNames.includes(productName.toLowerCase()) ) {
            return drinkLogo
        }
        else {
            return defaultLogo
        }
        
    }
    return (
        <OrderSummaryWrapper>
            <Title>Order Summary</Title>
            <ItemsWrapper>
                <>
                {totalCost > 0 && 
                    <OrderTotal>
                        Total: ${parseFloat(totalCost).toFixed(2)}
                    </OrderTotal>}
                {orderItems && orderItems.map((item) => {
                    return (
                        <OrderItemWrapper>
                            <ItemAndPrice>
                                <img width={50} height={50} src={getImage(item.name)} />
                                <OrderDetails>
                                    <div>{item.quantity} </div>
                                    {item.size && <div>{item.size} </div>}
                                    <div>{item.name} </div>
                                    <div >${parseFloat(item.price).toFixed(2)}</div>
                                    </OrderDetails> 
                            </ItemAndPrice>
                            <Customization>
                            {item.customizations.length > 0 && 
                                <>  
                                    Customizations: {` ${item.customizations.join(', ')}`}
                                </>
                            }
                            </Customization>
                        </OrderItemWrapper>
                    )  
                })}
            </>
        </ItemsWrapper>
        </OrderSummaryWrapper>
    )
}

export default OrderSummary; 



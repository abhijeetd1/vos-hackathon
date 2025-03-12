import styled from "styled-components";

export const OrderSummaryWrapper = styled.div`
        border-radius: 5px; 
        padding: 30px; 
        width: 300px; 
        background: #ececec;
        border-top: 3px solid rgb(255, 188, 13);
`

export const Title = styled.div`
        font-size: 18px; 
        font-weight: 700; 
        padding-bottom: 30px;
`

export const OrderItemWrapper = styled.div`
        display: flex; 
        flex-direction: column; 
        gap: 10px; 
        align-items: center; 
        background: white; 
        border-radius: 5px; 
        padding: 10px;
        justify-content: flex-start;
        font-size: 14px;
`

export const ItemsWrapper = styled.div`
        display: flex; 
        flex-direction: column; 
        gap: 15px; 
`

export const Loader = styled.div`
    
    border-radius: 5px; 
    background-color: white; 
    display: flex; 
    flex-direction: row; 
    gap: 20px; 
    align-items: center; 
    padding: 10px;
    font-weight: 700;
    padding: 20px; 
`

export const ItemAndPrice = styled.div`
        display: flex; 
        flex-direction: row; 
        gap: 15px; 
        width: 100%;

`

export const Customization = styled.div`
        display: flex; 
        flex-direction: row; 
        font-size: 12px; 
        font-style: italic;

`

export const OrderDetails = styled.div`
        display: flex; 
        flex-direction: row; 
        gap: 5px; 
        font-weight: 700; 
        align-items: center;

`

export const OrderTotal = styled.div`
        padding-bottom: 15px;
        font-weight: 700; 
`
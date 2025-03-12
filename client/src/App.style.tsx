import styled from "styled-components";


export const MainContainer = styled.div`
    background-color: white;
    display: flex; 
    flex-direction: column; 
    gap: 60px; 
    align-items: center; 
    justify-content: center; 


`

export const Title = styled.div`
    font-size: 20px; 
    height: 50px; 
    background-color: white;
    width: 100%; 
    color: black; 
    font-weight: 700; 
        padding: 20px; 
        display: flex; 
        flex-direction: row; 
        justify-content: center; 
        align-items: center; 
        position: sticky;
        top: 0; 
        box-shadow: rgba(0, 0, 0, 0.25) 0px 0px 35px;
        font-family: Speedee, -apple-system, sans-serif;
        display: flex; 
        flex-direction: row; 
        gap: 20px; 




`

export const Column = styled.div`
    display: flex; 
    flex-direction: column; 
    align-items: flex-start; 
    gap: 40px; 
    width: 700px; 
`

export const Row = styled.div`
    display: flex; 
    flex-direction: row; 
    width: 100%; 
    justify-content: space-evenly; 



`
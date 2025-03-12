import styled, { keyframes, css } from 'styled-components';

// Define the keyframes with the `keyframes` helper
const moveBorder = keyframes`
  0% {
    box-shadow: 0 0 0 4px rgb(255, 188, 13);
  }
  50% {
    box-shadow: 0 0 0 10px rgb(255, 188, 13);
  }
  100% {
    box-shadow: 0 0 0 4px rgb(255, 188, 13);
  }
`;

export const StyledIcon = styled.img`
        width: 40px; 
        height: 40px; 
        background-color: #242424;
        display: block;
        border: 4px solid transparent;
        border-radius: 50px; /* Makes the image circular */

        /* Conditionally apply animation using props */
        ${(props) => props.isRecording && css`
        animation: ${moveBorder} 1.5s infinite ease-in-out; /* Apply the animation when recording */
        `}
`;



export const StyledButton = styled.button`
        border: none; 
        background: white; 
        display: flex;
        cursor: pointer; 
`

export const ButtonWrapper = styled.div`
        display: flex; 
        flex-direction: row; 
        align-items: center; 
        gap: 10px; 
`

export const VoiceRecorderWrapper = styled.div`
        display: flex; 
        flex-direction: column; 
        gap: 20px; 
        align-items: flex-start;
        justify-content: center;
        width: 100%; 
        border-radius: 5px; 
        p {
            margin: 5px; 
            font-weight: 700;
        }
`
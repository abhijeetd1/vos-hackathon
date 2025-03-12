import React, { useState } from 'react';
import './App.css';
import VoiceRecorder from './components/voiceRecorder/VoiceRecorder.tsx';
import { Column, MainContainer, Row, Title } from './App.style.tsx';
import OrderSummary from './components/orderSummary/OrderSummary.tsx';
import ProductDisplay from './components/productDisplay/ProductDisplay.tsx';
import logo from './download.png'; 

function App() {
  const [recording, setRecording] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>('');

  const [waitingForTranscript, setWaitingForTranscript] = useState<boolean>(false)
  return (

    <div className="App">
      <MainContainer>
        <Title>
          <img src={logo} alt='mcd-logo' width={30} height={30}/>
          <p>Voice Order Assistant</p>
          </Title>
          <Row>
          <Column>
            <VoiceRecorder setTranscript={setTranscript} setRecording={setRecording} recording={recording} setWaitingForTranscript={setWaitingForTranscript} />
            <ProductDisplay transcript={transcript} recording={recording} waitingForTranscript={waitingForTranscript}/>
          </Column>
            <OrderSummary/>
          </Row>
      </MainContainer>
    </div>
  );
}

export default App;



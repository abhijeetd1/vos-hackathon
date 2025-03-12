import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import audio from '../../recorder.png'; 
import { ButtonWrapper, StyledButton, StyledIcon, VoiceRecorderWrapper } from './VoiceRecorder.style.tsx';
import { LiveAudioVisualizer } from 'react-audio-visualize';
import { useSelector, useDispatch } from 'react-redux'
import { setCustomizationItems, setFoodItems, setDrinkItems, addPrompt, updatePrompt, clearPrompts, setNextAudioNew, setTotalCost } from '../../slices/orders.ts';
import { v4 as uuidv4 } from 'uuid';
import { Microphone as ReactComponent} from '../../microphone-svgrepo-com.svg'

const blobToBase64 = (blob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
};

type VoiceRecorderProps =  {
    setTranscript: (content: string) => void; 
    setRecording: (content: boolean) => void; 
    recording: boolean; 
    setWaitingForTranscript: (content: boolean) => void;
}

const playFulfillmentText = async (text: string) => {
  try {
    const response = await axios.post('http://localhost:5000/synthesize', { text }, { responseType: 'arraybuffer' });
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const audioBuffer = await audioContext.decodeAudioData(response.data);
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);
    source.start(0);
  } catch (error) {
    console.error('Error playing fulfillment text:', error);
  }
};

function removeQuotes(inputString: string): string {
  return inputString.replace(/"/g, '');
}

const VoiceRecorder = ({setTranscript, setRecording, recording, setWaitingForTranscript}: VoiceRecorderProps) => {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder>();
  const [sessionId, setSessionId] = useState(uuidv4()); // Generate a new session ID
  const dispatch = useDispatch()

  const handleAudioCapture = async () => {
    if (!recording) {
      setRecording(true);
      audioChunksRef.current = [];
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        setMediaRecorder(mediaRecorderRef.current);
        mediaRecorderRef.current.ondataavailable = (event) => {
        
          audioChunksRef.current.push(event.data);
        };
        mediaRecorderRef.current.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const audioBase64 = await blobToBase64(audioBlob);
          await sendAudioToBackend(audioBase64);
        };

        mediaRecorderRef.current.start();
      } catch (error) {
        console.error('Error accessing microphone:', error);
      }
    } else {
      setRecording(false);
      mediaRecorderRef.current?.stop();
    }
  };

  const nextAudioNew = useSelector((state : any) => state.orders.nextAudioNew)


  const sendAudioToBackend = async (audioBase64: string) => {

    try {
      if (nextAudioNew) {
        // clear conversation, food items, and cost as it is a new session. 
        dispatch(clearPrompts());
        dispatch(setFoodItems([]));
        dispatch(setTotalCost(null));
      }
      setWaitingForTranscript(true)

      // Send request to transcribe the users audio 
      const response = await axios.post('http://localhost:5000/transcribe', { audio: audioBase64 });
      if (response.data && response.data.transcription) {
        setTranscript(response.data.transcription);
        dispatch(addPrompt({prompt: response.data.transcription, fulfillmentText: null } ));
        // once we recieve the transcription, send request to dialog flow
        let fulfillment = await axios.post('http://localhost:5000/detect-intent', {
           query: response.data.transcription, sessionId: sessionId, 
           isNewOrder: nextAudioNew
           }); 
        // once we recieve the response, update state to store all the new products, cost, etc. 
        if (fulfillment.data.fulfillmentText) {
          dispatch(setNextAudioNew(false));
            if (fulfillment.data.fulfillmentText.includes('payment')) {
              dispatch(setNextAudioNew(true));
            }           
            await playFulfillmentText(fulfillment.data.fulfillmentText);
            dispatch(updatePrompt({prompt: response.data.transcription, fulfillmentText: removeQuotes(fulfillment.data.fulfillmentText) } ));
            dispatch(setFoodItems(fulfillment.data.foodItems));
            dispatch(setTotalCost(fulfillment.data.total))
        }
        setWaitingForTranscript(false)
      }

      setWaitingForTranscript(false)
    } catch (error) {
      console.error('Error sending audio to backend:', error);
    }
  };

  return (
    <VoiceRecorderWrapper>
      <p>Welcome! Press the button below to begin placing your order </p>
      <ButtonWrapper>
          <StyledButton onClick={handleAudioCapture}>
            <StyledIcon isRecording={recording}src={audio} alt='recording-icon'/>
          </StyledButton>
      </ButtonWrapper>
    </VoiceRecorderWrapper>
  );
};

export default VoiceRecorder;



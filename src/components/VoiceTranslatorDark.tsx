import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Mic, Globe, Wifi, WifiOff } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface TranslationStep {
  step: 'idle' | 'recording' | 'transcribing' | 'translating' | 'synthesizing' | 'complete' | 'error';
  progress: number;
  text?: string;
}

const LANGUAGES = [
  { code: 'en', name: 'English', fullName: 'English (English)' },
  { code: 'es', name: 'Spanish', fullName: 'Español (Spanish)' },
  { code: 'fr', name: 'French', fullName: 'Français (French)' },
  { code: 'de', name: 'German', fullName: 'Deutsch (German)' },
  { code: 'it', name: 'Italian', fullName: 'Italiano (Italian)' },
  { code: 'pt', name: 'Portuguese', fullName: 'Português (Portuguese)' },
  { code: 'ru', name: 'Russian', fullName: 'Русский (Russian)' },
  { code: 'ja', name: 'Japanese', fullName: '日本語 (Japanese)' },
  { code: 'ko', name: 'Korean', fullName: '한국어 (Korean)' },
  { code: 'zh', name: 'Chinese', fullName: '中文 (Chinese)' },
];

export default function VoiceTranslatorDark() {
  const [sourceLanguage, setSourceLanguage] = useState('en');
  const [targetLanguage, setTargetLanguage] = useState('es');
  const [translationStep, setTranslationStep] = useState<TranslationStep>({ step: 'idle', progress: 0 });
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [originalText, setOriginalText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const { toast } = useToast();

  // Initialize API key
  const getApiKey = () => {
    const providedApiKey = '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';
    const storedApiKey = localStorage.getItem('groq_api_key');
    
    if (!storedApiKey) {
      localStorage.setItem('groq_api_key', providedApiKey);
      return providedApiKey;
    }
    return storedApiKey;
  };

  const handleConnect = async () => {
    try {
      // Test microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      setIsConnected(true);
      toast({
        title: "Connected Successfully",
        description: "Ready to start translating",
      });
    } catch (error) {
      toast({
        title: "Connection Failed",
        description: "Could not access microphone. Please check permissions.",
        variant: "destructive",
      });
    }
  };

  const startRecording = async () => {
    if (!isConnected) {
      toast({
        title: "Not Connected",
        description: "Please connect first to start translating",
        variant: "destructive",
      });
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      const chunks: BlobPart[] = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        await processAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setTranslationStep({ step: 'recording', progress: 0 });

    } catch (error) {
      console.error('Error accessing microphone:', error);
      toast({
        title: "Microphone Error",
        description: "Could not access microphone. Please check permissions.",
        variant: "destructive",
      });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processAudio = async (audioBlob: Blob) => {
    const apiKey = getApiKey();
    
    try {
      // Step 1: Speech to Text
      setTranslationStep({ step: 'transcribing', progress: 25 });
      const transcription = await speechToText(audioBlob, apiKey);
      setOriginalText(transcription);

      // Step 2: Translation
      setTranslationStep({ step: 'translating', progress: 50 });
      const translation = await translateText(transcription, sourceLanguage, targetLanguage, apiKey);
      setTranslatedText(translation);

      // Step 3: Text to Speech
      setTranslationStep({ step: 'synthesizing', progress: 75 });
      
      setTranslationStep({ step: 'complete', progress: 100 });
      
      // Auto-play translation
      setTimeout(() => {
        playTranslation(translation);
      }, 500);

    } catch (error) {
      console.error('Processing error:', error);
      setTranslationStep({ step: 'error', progress: 0 });
      toast({
        title: "Translation Error",
        description: "Failed to process audio. Please try again.",
        variant: "destructive",
      });
    }
  };

  const speechToText = async (audioBlob: Blob, apiKey: string): Promise<string> => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'audio.webm');
    formData.append('model', 'whisper-large-v3-turbo');
    formData.append('response_format', 'verbose_json');
    formData.append('temperature', '0');

    const response = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`STT API error: ${response.status}`);
    }

    const result = await response.json();
    return result.text || 'No transcription available';
  };

  const translateText = async (text: string, sourceLang: string, targetLang: string, apiKey: string): Promise<string> => {
    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'llama-3.3-70b-versatile',
        messages: [
          {
            role: 'system',
            content: `Translate the input text from ${sourceLang} to ${targetLang}, preserving tone and meaning. Return only the translated text, no explanations or additional formatting.`
          },
          {
            role: 'user',
            content: text
          }
        ],
        temperature: 0.3,
        max_tokens: 1000
      }),
    });

    if (!response.ok) {
      throw new Error(`Translation API error: ${response.status}`);
    }

    const result = await response.json();
    return result.choices[0]?.message?.content || 'Translation failed';
  };

  const playTranslation = (text: string) => {
    if ('speechSynthesis' in window && text) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = targetLanguage === 'en' ? 'en-US' : 
                       targetLanguage === 'es' ? 'es-ES' :
                       targetLanguage === 'fr' ? 'fr-FR' :
                       targetLanguage === 'de' ? 'de-DE' :
                       targetLanguage === 'it' ? 'it-IT' :
                       targetLanguage === 'pt' ? 'pt-PT' :
                       targetLanguage === 'ru' ? 'ru-RU' :
                       targetLanguage === 'ja' ? 'ja-JP' :
                       targetLanguage === 'ko' ? 'ko-KR' :
                       targetLanguage === 'zh' ? 'zh-CN' : 'en-US';
      
      speechSynthesis.speak(utterance);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
              <Globe className="h-6 w-6 text-primary" />
            </div>
            <h1 className="text-4xl font-bold">
              <span className="text-primary">Real Time AI</span>{' '}
              <span className="text-foreground">Voice Translation</span>
            </h1>
          </div>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto leading-relaxed">
            Real-time voice translation powered by Groq AI. Speak in your language, be understood in 
            any language. Connect with people around the world instantly.
          </p>
        </div>

        {/* Connection Status */}
        <div className="flex items-center justify-between mb-8 p-4 rounded-lg bg-card/50 border border-border/50">
          <div className="flex items-center gap-3">
            {isConnected ? (
              <>
                <Wifi className="h-5 w-5 text-secondary" />
                <span className="text-secondary font-medium">Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="h-5 w-5 text-muted-foreground" />
                <span className="text-muted-foreground font-medium">Not connected</span>
              </>
            )}
          </div>
          {!isConnected && (
            <Button 
              onClick={handleConnect}
              className="bg-primary hover:bg-primary/90 text-white px-6"
            >
              Connect
            </Button>
          )}
        </div>

        {/* Language Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          <div className="space-y-3">
            <label className="text-sm font-medium text-primary flex items-center gap-2">
              <Globe className="h-4 w-4" />
              Your Language
            </label>
            <Select value={sourceLanguage} onValueChange={setSourceLanguage}>
              <SelectTrigger className="w-full bg-card border-border text-foreground h-12">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-card border-border">
                {LANGUAGES.map((lang) => (
                  <SelectItem key={lang.code} value={lang.code} className="text-foreground hover:bg-muted">
                    {lang.fullName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-3">
            <label className="text-sm font-medium text-primary flex items-center gap-2">
              <Globe className="h-4 w-4" />
              Target Language
            </label>
            <Select value={targetLanguage} onValueChange={setTargetLanguage}>
              <SelectTrigger className="w-full bg-card border-border text-foreground h-12">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-card border-border">
                {LANGUAGES.map((lang) => (
                  <SelectItem key={lang.code} value={lang.code} className="text-foreground hover:bg-muted">
                    {lang.fullName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Voice Translation Interface */}
        <div className="text-center mb-12">
          <h2 className="text-xl font-semibold mb-8 text-foreground">Voice Translation</h2>
          
          {/* Microphone Button */}
          <div className="flex justify-center mb-6">
            <Button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={!isConnected}
              className={`
                w-24 h-24 rounded-full transition-all duration-300
                ${isRecording 
                  ? 'bg-destructive hover:bg-destructive/90 animate-pulse' 
                  : isConnected
                  ? 'bg-primary hover:bg-primary/90 hover:scale-110 shadow-lg hover:shadow-primary/25'
                  : 'bg-muted text-muted-foreground cursor-not-allowed'
                }
              `}
            >
              <Mic className="h-8 w-8" />
            </Button>
          </div>

          {/* Status Text */}
          <p className="text-muted-foreground text-lg">
            {!isConnected 
              ? 'Connect to start translating'
              : isRecording 
              ? 'Recording... Click to stop'
              : translationStep.step === 'transcribing'
              ? 'Converting speech to text...'
              : translationStep.step === 'translating'
              ? 'Translating...'
              : translationStep.step === 'synthesizing'
              ? 'Generating speech...'
              : translationStep.step === 'complete'
              ? 'Translation complete!'
              : 'Hold the microphone and speak'
            }
          </p>
        </div>

        {/* Results Display */}
        {(originalText || translatedText) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
            <div className="p-6 bg-card/50 border border-border/50 rounded-lg">
              <h3 className="font-semibold mb-3 text-foreground">Original</h3>
              <p className="text-muted-foreground">{originalText || 'Your speech will appear here...'}</p>
            </div>
            <div className="p-6 bg-card/50 border border-border/50 rounded-lg">
              <h3 className="font-semibold mb-3 text-foreground">Translation</h3>
              <p className="text-muted-foreground">{translatedText || 'Translation will appear here...'}</p>
            </div>
          </div>
        )}

        {/* How it works */}
        <div className="text-center">
          <h3 className="text-lg font-semibold mb-4 text-foreground">How it works</h3>
          <div className="text-sm text-muted-foreground space-y-1">
            <p>1. Connect to the translation room • 2. Select your languages • 3. Hold the microphone and speak • 4. Listen to the real-time translation</p>
            <p className="text-xs mt-3">Powered by Groq AI for accurate translations and browser APIs for voice processing</p>
          </div>
        </div>
      </div>
    </div>
  );
}
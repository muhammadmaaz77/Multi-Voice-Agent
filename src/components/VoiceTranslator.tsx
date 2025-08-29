import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Mic, MicOff, Play, Pause, Volume2, Globe, ArrowRight } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface TranslationStep {
  step: 'idle' | 'recording' | 'transcribing' | 'translating' | 'synthesizing' | 'complete' | 'error';
  progress: number;
  text?: string;
}

const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Spanish', flag: '🇪🇸' },
  { code: 'fr', name: 'French', flag: '🇫🇷' },
  { code: 'de', name: 'German', flag: '🇩🇪' },
  { code: 'it', name: 'Italian', flag: '🇮🇹' },
  { code: 'pt', name: 'Portuguese', flag: '🇵🇹' },
  { code: 'ru', name: 'Russian', flag: '🇷🇺' },
  { code: 'ja', name: 'Japanese', flag: '🇯🇵' },
  { code: 'ko', name: 'Korean', flag: '🇰🇷' },
  { code: 'zh', name: 'Chinese', flag: '🇨🇳' },
];

export default function VoiceTranslator() {
  const [sourceLanguage, setSourceLanguage] = useState('en');
  const [targetLanguage, setTargetLanguage] = useState('es');
  const [translationStep, setTranslationStep] = useState<TranslationStep>({ step: 'idle', progress: 0 });
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [originalText, setOriginalText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const { toast } = useToast();

  // Initialize API key from localStorage or use provided key
  const getApiKey = () => {
    const providedApiKey = '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';
    const storedApiKey = localStorage.getItem('groq_api_key');
    
    if (!storedApiKey) {
      localStorage.setItem('groq_api_key', providedApiKey);
      return providedApiKey;
    }
    return storedApiKey;
  };

  const startRecording = async () => {
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

      toast({
        title: "Recording started",
        description: "Speak now, click stop when finished",
      });
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

      // Step 3: Text to Speech (using Web Speech API)
      setTranslationStep({ step: 'synthesizing', progress: 75 });
      
      setTranslationStep({ step: 'complete', progress: 100 });
      
      toast({
        title: "Translation Complete",
        description: "Click play to hear the translation",
      });

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

  const textToSpeech = async (text: string, apiKey: string): Promise<string> => {
    // Using Web Speech API for immediate functionality
    return new Promise((resolve) => {
      resolve('speech-synthesis-ready');
    });
  };

  const playAudio = () => {
    if (translatedText) {
      setIsPlaying(true);
      const utterance = new SpeechSynthesisUtterance(translatedText);
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
      
      utterance.onend = () => setIsPlaying(false);
      speechSynthesis.speak(utterance);
    }
  };

  const stopAudio = () => {
    speechSynthesis.cancel();
    setIsPlaying(false);
  };

  const getStepText = () => {
    switch (translationStep.step) {
      case 'idle': return 'Ready to translate';
      case 'recording': return 'Recording your voice...';
      case 'transcribing': return 'Converting speech to text...';
      case 'translating': return 'Translating text...';
      case 'synthesizing': return 'Generating speech...';
      case 'complete': return 'Translation complete!';
      case 'error': return 'Error occurred';
      default: return 'Processing...';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-subtle p-4">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4 animate-fade-in">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Globe className="h-8 w-8 text-primary" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Voice Translator
            </h1>
          </div>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Speak in any language and hear real-time translations with natural-sounding speech
          </p>
        </div>

        {/* Language Selection */}
        <Card className="p-6 shadow-card animate-slide-up">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">From</label>
              <Select value={sourceLanguage} onValueChange={setSourceLanguage}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LANGUAGES.map((lang) => (
                    <SelectItem key={lang.code} value={lang.code}>
                      <span className="flex items-center gap-2">
                        <span>{lang.flag}</span>
                        <span>{lang.name}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex justify-center">
              <ArrowRight className="h-6 w-6 text-muted-foreground" />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">To</label>
              <Select value={targetLanguage} onValueChange={setTargetLanguage}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LANGUAGES.map((lang) => (
                    <SelectItem key={lang.code} value={lang.code}>
                      <span className="flex items-center gap-2">
                        <span>{lang.flag}</span>
                        <span>{lang.name}</span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </Card>

        {/* Recording Interface */}
        <Card className="p-8 text-center shadow-elegant animate-slide-up">
          <div className="space-y-6">
            {/* Record Button */}
            <div className="flex justify-center">
              <Button
                variant={isRecording ? "destructive" : "record"}
                size="lg"
                onClick={isRecording ? stopRecording : startRecording}
                className={`h-20 w-20 rounded-full ${isRecording ? 'animate-pulse-glow' : ''}`}
                disabled={translationStep.step !== 'idle' && translationStep.step !== 'complete' && translationStep.step !== 'error'}
              >
                {isRecording ? <MicOff className="h-8 w-8" /> : <Mic className="h-8 w-8" />}
              </Button>
            </div>

            {/* Status */}
            <div className="space-y-3">
              <p className="text-lg font-medium">{getStepText()}</p>
              {translationStep.step !== 'idle' && translationStep.step !== 'error' && (
                <Progress value={translationStep.progress} className="w-full max-w-md mx-auto" />
              )}
            </div>
          </div>
        </Card>

        {/* Results */}
        {(originalText || translatedText) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-slide-up">
            {/* Original Text */}
            <Card className="p-6 shadow-card">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg">
                    {LANGUAGES.find(l => l.code === sourceLanguage)?.flag}
                  </span>
                  <h3 className="font-semibold">Original</h3>
                </div>
                <p className="text-muted-foreground min-h-[60px] p-3 bg-muted/50 rounded-md">
                  {originalText || 'Your speech will appear here...'}
                </p>
              </div>
            </Card>

            {/* Translated Text */}
            <Card className="p-6 shadow-card">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">
                      {LANGUAGES.find(l => l.code === targetLanguage)?.flag}
                    </span>
                    <h3 className="font-semibold">Translation</h3>
                  </div>
                  {translatedText && (
                    <Button
                      variant="success"
                      size="sm"
                      onClick={isPlaying ? stopAudio : playAudio}
                      disabled={!translatedText}
                    >
                      {isPlaying ? <Pause className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                    </Button>
                  )}
                </div>
                <p className="text-muted-foreground min-h-[60px] p-3 bg-muted/50 rounded-md">
                  {translatedText || 'Translation will appear here...'}
                </p>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
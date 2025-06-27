'use client'

import { Button } from '@/components/ui/button'
import { ButtonFixed } from '@/components/ui/button-fixed'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useState, useRef, useEffect } from 'react'

export default function TestButtonDiagnosticPage() {
  const [events, setEvents] = useState<string[]>([])
  const buttonRef = useRef<HTMLButtonElement>(null)
  const nativeButtonRef = useRef<HTMLButtonElement>(null)

  const logEvent = (message: string) => {
    console.log(message)
    setEvents(prev => [...prev, `${new Date().toISOString().split('T')[1]}: ${message}`])
  }

  useEffect(() => {
    // 診断情報を表示
    logEvent('Page loaded - Diagnostic started')
    
    // Buttonコンポーネントの詳細を確認
    if (buttonRef.current) {
      logEvent(`Button ref exists: ${!!buttonRef.current}`)
      logEvent(`Button tagName: ${buttonRef.current.tagName}`)
      logEvent(`Button disabled: ${buttonRef.current.disabled}`)
      logEvent(`Button tabIndex: ${buttonRef.current.tabIndex}`)
      
      // イベントリスナーを直接追加してテスト
      const directClickHandler = () => logEvent('Direct event listener fired on Button')
      buttonRef.current.addEventListener('click', directClickHandler)
      
      return () => {
        buttonRef.current?.removeEventListener('click', directClickHandler)
      }
    }
  }, [])

  const handleButtonClick = (e: React.MouseEvent) => {
    logEvent(`React onClick fired - target: ${(e.target as HTMLElement).tagName}, currentTarget: ${(e.currentTarget as HTMLElement).tagName}`)
    logEvent(`Event phase: ${e.eventPhase}, bubbles: ${e.bubbles}`)
    logEvent(`Is defaultPrevented: ${e.defaultPrevented}`)
  }

  const handleCapture = (e: React.MouseEvent) => {
    logEvent(`Capture phase - target: ${(e.target as HTMLElement).tagName}`)
  }

  return (
    <div className="container mx-auto p-8 max-w-6xl">
      <h1 className="text-2xl font-bold mb-4">Button Click Diagnostic in Tabs</h1>
      
      <div className="grid grid-cols-2 gap-8">
        <div>
          <Tabs defaultValue="test" className="w-full">
            <TabsList>
              <TabsTrigger value="test">Test Tab</TabsTrigger>
              <TabsTrigger value="other">Other Tab</TabsTrigger>
            </TabsList>
            
            <TabsContent 
              value="test" 
              className="space-y-4 border p-4 rounded"
              onClickCapture={handleCapture}
            >
              <h2 className="text-lg font-semibold">Inside TabsContent</h2>
              
              <div className="space-y-4">
                {/* Original Button Component */}
                <div className="border p-3 rounded bg-gray-50">
                  <p className="text-sm font-medium mb-2">1. Original Button Component:</p>
                  <Button 
                    ref={buttonRef}
                    onClick={handleButtonClick}
                    onMouseDown={() => logEvent('Button onMouseDown')}
                    onMouseUp={() => logEvent('Button onMouseUp')}
                    onPointerDown={() => logEvent('Button onPointerDown')}
                    onPointerUp={() => logEvent('Button onPointerUp')}
                  >
                    Click Me (Button Component)
                  </Button>
                </div>

                {/* Fixed Button Component */}
                <div className="border p-3 rounded bg-blue-50">
                  <p className="text-sm font-medium mb-2">2. Fixed Button Component:</p>
                  <ButtonFixed 
                    onClick={(e) => {
                      logEvent('ButtonFixed clicked!')
                      handleButtonClick(e)
                    }}
                  >
                    Click Me (Fixed Button)
                  </ButtonFixed>
                </div>

                {/* Native button */}
                <div className="border p-3 rounded bg-green-50">
                  <p className="text-sm font-medium mb-2">3. Native button element:</p>
                  <button
                    ref={nativeButtonRef}
                    onClick={handleButtonClick}
                    className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                  >
                    Click Me (Native)
                  </button>
                </div>

                {/* Button with inline handler */}
                <div className="border p-3 rounded bg-yellow-50">
                  <p className="text-sm font-medium mb-2">4. Button with inline handler:</p>
                  <Button 
                    onClick={() => {
                      logEvent('Inline handler executed!')
                      alert('Inline handler worked!')
                    }}
                  >
                    Click Me (Inline)
                  </Button>
                </div>

                {/* Button with type="button" explicitly */}
                <div className="border p-3 rounded bg-purple-50">
                  <p className="text-sm font-medium mb-2">5. Button with type="button":</p>
                  <Button 
                    type="button"
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      logEvent('Button with type="button" clicked')
                    }}
                  >
                    Click Me (type="button")
                  </Button>
                </div>

                {/* Wrapped in a div with onClick */}
                <div className="border p-3 rounded bg-pink-50">
                  <p className="text-sm font-medium mb-2">6. Button wrapped in div:</p>
                  <div onClick={() => logEvent('Parent div clicked')}>
                    <Button 
                      onClick={(e) => {
                        e.stopPropagation()
                        logEvent('Wrapped button clicked')
                      }}
                    >
                      Click Me (Wrapped)
                    </Button>
                  </div>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="other">
              <p>Switch back to Test Tab to continue testing</p>
            </TabsContent>
          </Tabs>
        </div>

        <div>
          <h2 className="text-lg font-semibold mb-4">Event Log:</h2>
          <div className="bg-gray-900 text-gray-100 p-4 rounded font-mono text-xs h-[600px] overflow-y-auto">
            {events.length === 0 ? (
              <p className="text-gray-400">Waiting for events...</p>
            ) : (
              events.map((event, idx) => (
                <div key={idx} className="mb-1">{event}</div>
              ))
            )}
          </div>
          <button 
            onClick={() => setEvents([])}
            className="mt-2 text-sm text-gray-500 hover:text-gray-700"
          >
            Clear Log
          </button>
        </div>
      </div>

      <div className="mt-8 p-4 bg-blue-50 rounded">
        <h3 className="font-semibold mb-2">診断手順:</h3>
        <ol className="list-decimal list-inside space-y-1 text-sm">
          <li>各ボタンをクリックして、イベントログを確認</li>
          <li>どのボタンでクリックイベントが発火するか確認</li>
          <li>イベントの詳細（target, phase, etc.）を確認</li>
          <li>コンソールログも確認（F12 → Console）</li>
        </ol>
      </div>
    </div>
  )
}
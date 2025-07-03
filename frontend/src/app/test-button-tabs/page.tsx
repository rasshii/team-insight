'use client'

import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useState } from 'react'

export default function TestButtonTabsPage() {
  const [count, setCount] = useState(0)
  const [messages, setMessages] = useState<string[]>([])

  const addMessage = (message: string) => {
    setMessages(prev => [...prev, `${new Date().toISOString()}: ${message}`])
  }

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-2xl font-bold mb-4">Button in Tabs Test</h1>
      
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-2">Outside Tabs</h2>
        <div className="space-x-4">
          <Button 
            onClick={() => {
              addMessage('Button outside tabs clicked')
              setCount(c => c + 1)
            }}
          >
            Regular Button (Count: {count})
          </Button>
          
          <button
            onClick={() => addMessage('Native button outside tabs clicked')}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Native Button
          </button>
        </div>
      </div>

      <Tabs defaultValue="tab1" className="w-full">
        <TabsList>
          <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          <TabsTrigger value="tab2">Tab 2</TabsTrigger>
        </TabsList>
        
        <TabsContent value="tab1" className="space-y-4">
          <h2 className="text-xl font-semibold">Inside Tab 1</h2>
          
          <div className="space-y-2">
            <div>
              <Button 
                onClick={() => {
                  addMessage('Button in tab1 clicked')
                  setCount(c => c + 1)
                }}
              >
                Button Component (Count: {count})
              </Button>
            </div>
            
            <div>
              <Button 
                variant="outline"
                onClick={() => addMessage('Outline button in tab1 clicked')}
              >
                Outline Button
              </Button>
            </div>
            
            <div>
              <Button 
                disabled
                onClick={() => addMessage('This should not appear')}
              >
                Disabled Button
              </Button>
            </div>
            
            <div>
              <button
                onClick={() => addMessage('Native button in tab1 clicked')}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
              >
                Native Button
              </button>
            </div>
            
            <div>
              <Button 
                asChild
                onClick={() => addMessage('Button with asChild clicked')}
              >
                <span>Button with asChild</span>
              </Button>
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="tab2" className="space-y-4">
          <h2 className="text-xl font-semibold">Inside Tab 2</h2>
          
          <Button 
            onClick={() => {
              addMessage('Button in tab2 clicked')
              setCount(c => c + 1)
            }}
          >
            Another Button (Count: {count})
          </Button>
        </TabsContent>
      </Tabs>

      <div className="mt-8">
        <h3 className="text-lg font-semibold mb-2">Event Log:</h3>
        <div className="bg-gray-100 p-4 rounded max-h-60 overflow-y-auto">
          {messages.length === 0 ? (
            <p className="text-gray-500">No events yet. Click buttons to test.</p>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className="text-sm font-mono">{msg}</div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
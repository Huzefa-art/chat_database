import { Message } from '../types';
import ChartDisplay from './ChartDisplay';
import './MessageBubble.css';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.type === 'user';

  return (
    <div className={`message-row ${isUser ? 'user-row' : 'assistant-row'}`}>
      <div className="avatar-container">
        {isUser ? (
          <div className="user-avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
          </div>
        ) : (
          <div className="assistant-avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
            </svg>
          </div>
        )}
      </div>
      <div className="message-body">
        <div className="message-sender-name">{isUser ? 'You' : 'Assistant'}</div>

        {/* If it's a bot message with an erpResponse, the summary is handled below. Otherwise show content. */}
        {(!message.erpResponse) && <div className="message-text">{message.content}</div>}

        {message.erpResponse && (
          <div className="erp-response-area">
            <div className="response-summary-text">{message.erpResponse.summary || message.content}</div>
            {message.erpResponse.data.length > 0 && (
              <ChartDisplay erpResponse={message.erpResponse} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

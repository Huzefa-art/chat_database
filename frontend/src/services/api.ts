import { ERPResponse, APIRequest } from '../types';

const API_BASE_URL = 'http://localhost:8000';

// Storage helpers
export const setUserData = (user_id: number, username: string) => {
  localStorage.setItem('user_id', user_id.toString());
  localStorage.setItem('username', username);
};

export const getUserId = () => {
  const id = localStorage.getItem('user_id');
  return id ? parseInt(id, 10) : null;
};

export const getUsername = () => localStorage.getItem('username');

export const clearUserData = () => {
  localStorage.removeItem('user_id');
  localStorage.removeItem('username');
  localStorage.removeItem('current_chat_id');
};

export const isAuthenticated = () => !!getUserId();

// Auth API calls
export async function login(credentials: any) {
  const response = await fetch(`${API_BASE_URL}/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Login failed');
  }
  const data = await response.json();
  setUserData(data.user_id, data.username);
  return data;
}

export async function signup(userData: any) {
  const response = await fetch(`${API_BASE_URL}/signup/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Signup failed');
  }
  return response.json();
}

export async function createChat(title?: string) {
  const userId = getUserId();
  if (!userId) throw new Error('User not logged in');

  const response = await fetch(`${API_BASE_URL}/create-chat/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, title }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to create chat');
  }

  const data = await response.json();
  localStorage.setItem('current_chat_id', data.chat_id.toString());
  return data;
}

export async function loadChatHistory(chatId: number) {
  const response = await fetch(`${API_BASE_URL}/load-chathistory/?chat_id=${chatId}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to load chat history');
  }

  return response.json(); // Returns { messages: ERPResponse[] }
}

export async function queryERPData(question: string, chat_id: number): Promise<ERPResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/send-message/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question, chat_id } as APIRequest),
    });

    if (response.status === 401) {
      clearUserData();
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `API request failed: ${response.statusText}`);
    }

    const data = await response.json();
    return processERPResponse(data, question);
  } catch (error) {
    console.error('Error querying ERP data:', error);
    throw error;
  }
}

export async function listChats(userId: number) {
  const response = await fetch(`${API_BASE_URL}/list-chats/?user_id=${userId}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to list chats');
  }

  return response.json(); // Returns Array<{id: number, title: string, updated_at: string}>
}

export async function updateChat(chatId: number, title: string) {
  const response = await fetch(`${API_BASE_URL}/update-chat/${chatId}/`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to update chat');
  }

  return response.json();
}

export async function deleteChat(chatId: number) {
  const response = await fetch(`${API_BASE_URL}/delete-chat/${chatId}/`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to delete chat');
  }

  return response.json();
}

function processERPResponse(rawData: any, _question: string): ERPResponse {
  // If the backend provided the full expected structure, use it directly
  if (rawData.summary !== undefined && rawData.data !== undefined && rawData.chart !== undefined) {
    return rawData as ERPResponse;
  }

  // Fallback for unexpected formats
  return {
    summary: rawData.summary || String(rawData),
    data: rawData.data || [],
    chart: rawData.chart || {
      type: null,
      labels: [],
      datasets: [],
    },
  };
}

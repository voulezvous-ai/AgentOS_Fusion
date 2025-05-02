// src/components/InputBar.test.jsx  
import React from 'react';  
import { render, screen, fireEvent } from '@testing-library/react';  
import userEvent from '@testing-library/user-event';  
import { describe, it, expect, vi, beforeEach } from 'vitest'; // Funções do Vitest  
import InputBar from './InputBar'; // Importar o componente real

describe('InputBar Component', () => {  
  let setDraftMock;  
  let sendActionMock;

  beforeEach(() => {  
    // Reset mocks antes de cada teste  
    setDraftMock = vi.fn();  
    sendActionMock = vi.fn();  
  });

  it('renders correctly with placeholder and initially disabled button', () => {  
    render(  
      <InputBar  
        draft=""  
        setDraft={setDraftMock}  
        sendAction={sendActionMock}  
        placeholder="Digite algo..."  
        disabled={false}  
      />  
    );  
    expect(screen.getByPlaceholderText('Digite algo...')).toBeInTheDocument();  
    // Verificar se o botão existe (pode ser pelo title ou role)  
    const sendButton = screen.getByRole('button', { name: /enviar mensagem/i }); // Usar title como accessible name  
    expect(sendButton).toBeInTheDocument();  
    // Botão deve estar desabilitado porque 'draft' está vazio  
    expect(sendButton).toBeDisabled();  
  });

  it('calls setDraft on textarea change', async () => {  
    const user = userEvent.setup();  
    render(  
      <InputBar  
        draft=""  
        setDraft={setDraftMock}  
        sendAction={sendActionMock}  
        disabled={false}  
      />  
    );  
    const textarea = screen.getByRole('textbox');  
    await user.type(textarea, 'Olá mundo');

    // Verificar se setDraft foi chamado corretamente  
    // userEvent.type chama o onChange para cada caractere  
    expect(setDraftMock).toHaveBeenCalledTimes('Olá mundo'.length);  
    // Verificar a última chamada (pode ser mais robusto que contar)  
    expect(setDraftMock).toHaveBeenLastCalledWith('Olá mundo');  
  });

  it('enables send button when draft is not empty', () => {  
     // Renderizar com draft não vazio  
    render(  
      <InputBar  
        draft="Texto presente"  
        setDraft={setDraftMock}  
        sendAction={sendActionMock}  
        disabled={false}  
      />  
    );  
    const sendButton = screen.getByRole('button', { name: /enviar mensagem/i });  
    expect(sendButton).toBeEnabled();  
  });

    it('disables send button when draft consists only of whitespace', () => {  
     render(  
      <InputBar  
        draft="   " // Apenas espaços  
        setDraft={setDraftMock}  
        sendAction={sendActionMock}  
        disabled={false}  
      />  
    );  
    const sendButton = screen.getByRole('button', { name: /enviar mensagem/i });  
    expect(sendButton).toBeDisabled();  
  });

  it('calls sendAction on send button click when enabled', async () => {  
    const user = userEvent.setup();  
    render(  
      <InputBar  
        draft="Texto para enviar"  
        setDraft={setDraftMock}  
        sendAction={sendActionMock}  
        disabled={false}  
      />  
    );  
    const sendButton = screen.getByRole('button', { name: /enviar mensagem/i });  
    expect(sendButton).toBeEnabled(); // Garantir que está habilitado

    await user.click(sendButton);

    expect(sendActionMock).toHaveBeenCalledTimes(1);  
  });

    it('does NOT call sendAction on button click when disabled', async () => {  
    const user = userEvent.setup();  
    render(  
      <InputBar  
        draft="" // Draft vazio desabilita  
        setDraft={setDraftMock}  
        sendAction={sendActionMock}  
        disabled={false}  
      />  
    );  
    const sendButton = screen.getByRole('button', { name: /enviar mensagem/i });  
    expect(sendButton).toBeDisabled();

    // Tentar clicar mesmo desabilitado  
    await user.click(sendButton).catch(() => {}); // Clicar em botão desabilitado pode dar erro ou não fazer nada

    expect(sendActionMock).not.toHaveBeenCalled();  
  });

  it('calls sendAction on Enter key press (without Shift) when draft is not empty', async () => {  
    const user = userEvent.setup();  
    render(  
      <InputBar  
        draft="Enviar com Enter"  
        setDraft={setDraftMock}  
        sendAction={sendActionMock}  
        disabled={false}  
      />  
    );  
    const textarea = screen.getByRole('textbox');  
    // Focar no textarea antes de simular tecla  
    textarea.focus();  
    await user.keyboard('{Enter}');

    expect(sendActionMock).toHaveBeenCalledTimes(1);  
  });

  it('does NOT call sendAction on Enter key press when draft is empty', async () => {  
    const user = userEvent.setup();  
    render(  
      <InputBar  
        draft=""  
        setDraft={setDraftMock}  
        sendAction={sendActionMock}  
        disabled={false}  
      />  
    );  
    const textarea = screen.getByRole('textbox');  
    textarea.focus();  
    await user.keyboard('{Enter}');

    expect(sendActionMock).not.toHaveBeenCalled();  
  });

    it('does NOT call sendAction on Shift+Enter key press (adds newline)', async () => {  
    const user = userEvent.setup();  
    render(  
      <InputBar  
        draft="Nova linha"  
        setDraft={setDraftMock}  
        sendAction={sendActionMock}  
        disabled={false}  
      />  
    );  
    const textarea = screen.getByRole('textbox');  
    textarea.focus();  
    // Simular Shift+Enter  
    await user.keyboard('{Shift>}{Enter}{/Shift}');

    expect(sendActionMock).not.toHaveBeenCalled();  
    // Verificar se setDraft foi chamado para adicionar a nova linha (efeito do Enter no textarea)  
    // O comportamento exato depende de como o navegador/React lida com o evento padrão  
    // O mais importante é que sendAction não foi chamado.  
    // Poderíamos verificar se o valor do textarea (se controlado) contém uma nova linha.  
    // expect(textarea.value).toContain('n'); // Requer que o componente atualize o value do textarea  
  });

  it('disables textarea and button when disabled prop is true', () => {  
    render(  
      <InputBar  
        draft="abc"  
        setDraft={setDraftMock}  
        sendAction={sendActionMock}  
        disabled={true} // Passar prop disabled  
      />  
    );  
    expect(screen.getByRole('textbox')).toBeDisabled();  
    expect(screen.getByRole('button', { name: /enviar mensagem/i })).toBeDisabled();  
  });

  it('textarea resizes height based on content (requires visual/integration test or complex mocking)', () => {  
     // Testar o auto-resize é difícil em testes unitários puros com JSDOM/HappyDOM  
     // pois eles não calculam layout/scrollHeight realisticamente.  
     // Esse tipo de teste é melhor feito com E2E (Cypress) ou testes visuais de regressão.  
     // Podemos fazer um teste básico de que o useEffect é chamado, mas não valida o resultado visual.  
     render(  
      <InputBar  
        draft="Linha1nLinha2nLinha3"  
        setDraft={setDraftMock}  
        sendAction={sendActionMock}  
        disabled={false}  
      />  
    );  
    const textarea = screen.getByRole('textbox');  
    // Verificar se o estilo inicial está lá (não valida se a altura *mudou* corretamente)  
    expect(textarea).toHaveStyle('min-height: 44px');  
    expect(textarea).toHaveStyle('max-height: 120px');  
    // Não podemos assertivamente verificar a altura calculada aqui.  
    expect(true).toBe(true); // Placeholder assertion  
  });

});


// Dentro do onmessage do WebSocket — adicionar suporte a 'executing_step'
case 'agent_command_update':
  const commandResult = data.payload;
  const jobId = commandResult?.job_id;

  if (jobId && commandResult.status) {
    if (commandResult.status === 'executing_step') {
      addCommandHistory({
        type: 'intermediate_step',
        role: 'system',
        text: commandResult.message,
        jobId: jobId,
        details: commandResult.details,
        status: commandResult.status
      });
      setActiveJobId(jobId);
    } else {
      updateCommandHistoryItem(jobId, {
        text: commandResult.message,
        details: commandResult.details,
        status: commandResult.status
      });
      if (useFusionStore.getState().activeJobId === jobId) {
        setActiveJobId(null);
      }
    }
  }

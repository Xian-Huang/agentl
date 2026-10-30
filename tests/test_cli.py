from unittest.mock import MagicMock, patch
import typer
from typer.testing import CliRunner
from agentl.cli import app

runner = CliRunner()

def test_chat_single_mode():

    with patch("agentl.cli.ReActAgent") as MockAgent:
        mock_agent = MagicMock()
        mock_agent.chat.return_value = {"content": "你好", "role": "assistant"}
        mock_agent.trace = []
        MockAgent.return_value = mock_agent

        result = runner.invoke(app, ["chat", "测试问题"])

        assert result.exit_code == 0
        assert "你好" in result.stdout
        mock_agent.chat.assert_called_once()


@app.callback()
def main(ctx: typer.Context): ...

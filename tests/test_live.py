import pytest
import subprocess

@pytest.mark.system
def test_help_option():
    result = subprocess.run(['python', '-m', 'rating', '--help'], capture_output=True, text=True)
    assert 'Fetches and prints a players' in result.stdout


@pytest.mark.system
def test_uscf_option():
    result = subprocess.run(['python', '-m', 'rating', 'someplayer', '--uscf'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'someplayer' in result.stdout


@pytest.mark.system
def test_lichess_option():
    result = subprocess.run(['python', '-m', 'rating', 'someplayer', '--lichess'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'someplayer' in result.stdout


@pytest.mark.system
def test_chesscom_option():
    result = subprocess.run(['python', '-m', 'rating', 'someplayer', '--chess'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'someplayer' in result.stdout


@pytest.mark.system
def test_fide_option():
    result = subprocess.run(['python', '-m', 'rating', '1503014', '--fide'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'Magnus' in result.stdout


@pytest.mark.system
def test_default_uscf():
    result = subprocess.run(['python', '-m', 'rating', 'someplayer'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'someplayer' in result.stdout


@pytest.mark.system
def test_invalid_option():
    result = subprocess.run(['python', '-m', 'rating', 'someplayer', '--invalid'], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'error' in result.stderr.lower()

import pandas as pd
import pytest
from src.preprocessing import FEATURES, validate_frame


def test_invalid_inputs():
    df = pd.DataFrame([[1, 0.2, 230, 5, 2, 1, -3]], columns=FEATURES)
    with pytest.raises(ValueError):
        validate_frame(df)

from weakref import WeakKeyDictionary


class StringValidator:
    def __init__(self) -> None:
        self._values = WeakKeyDictionary()

    def __get__(self, instance, owner):
        return self._values.get(instance)

    def __set__(self, instance, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Value must be a string")
        if not value.strip():
            raise ValueError("Value cannot be empty")
        self._values[instance] = value.strip()

    def __delete__(self, instance):
        if instance in self._values:
            del self._values[instance]
        else:
            raise AttributeError("String value not set")


class IntegerValidator:
    def __init__(self) -> None:
        self._values = WeakKeyDictionary()

    def __get__(self, instance, owner) -> int:
        return self._values.get(instance)

    def __set__(self, instance, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError("Value must be an integer")
        self._values[instance] = value

    def __delete__(self, instance):
        if instance in self._values:
            del self._values[instance]
        else:
            raise AttributeError("Integer value not set")


class PositiveIntegerValidator(IntegerValidator):
    def __set__(self, instance, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError("Value must be an integer")
        if value < 0:
            raise ValueError("Value must be positive")
        self._values[instance] = value


class FloatValidator:
    def __init__(self) -> None:
        self._values = WeakKeyDictionary()

    def __get__(self, instance, owner) -> float:
        return self._values.get(instance)

    def __set__(self, instance, value: float) -> None:
        if not isinstance(value, float):
            raise ValueError("Value must be a float")
        self._values[instance] = value

    def __delete__(self, instance):
        if instance in self._values:
            del self._values[instance]
        else:
            raise AttributeError("Float value not set")


class PositiveFloatValidator(FloatValidator):
    def __set__(self, instance, value: float) -> None:
        if not isinstance(value, float):
            raise ValueError("Value must be a float")
        if value < 0:
            raise ValueError("Value must be positive")
        self._values[instance] = value

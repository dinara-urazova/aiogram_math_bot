from aiogram import Bot, Dispatcher, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, StateFilter
from bot.config_reader import env_config
import asyncio
import logging
import sys
from math import sqrt

tg_token = env_config.telegram_token.get_secret_value()
logging.basicConfig(level=logging.INFO, stream=sys.stdout)


def try_to_get_number(text: str) -> float:
    return float(text.replace(",", "."))


class Logic(StatesGroup):
    need_first = State()
    need_operation = State()
    need_second = State()


dp = Dispatcher()


# Хэндлер на команду /start
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()  # очистить состояние
    await state.set_state(Logic.need_first)
    await message.answer(
        "Добро пожаловать! Пожалуйста, введите первое число.",
        reply_markup=ReplyKeyboardRemove(),
    )


@dp.message(StateFilter(Logic.need_first))
async def first_handler(message: Message, state: FSMContext) -> None:
    try:
        value = try_to_get_number(message.text)
    except ValueError:
        await message.answer("Введите число, пожалуйста.")
        return

    await state.update_data(first=value)
    await state.set_state(Logic.need_operation)

    builder = InlineKeyboardBuilder()
    builder.button(text="+", callback_data="add")
    builder.button(text="-", callback_data="subtract")
    builder.button(text="*", callback_data="multiply")
    builder.button(text="/", callback_data="divide")
    builder.button(text="x²", callback_data="square")
    builder.button(text="√x", callback_data="root")
    builder.adjust(3)

    await message.answer(
        "Принял, спасибо! Выберите операцию:", reply_markup=builder.as_markup()
    )


@dp.callback_query(
    StateFilter(Logic.need_operation),
    F.data.in_({"square", "root"}),
)
async def uniary_operation_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    first_num = data["first"]

    if callback.data == "square":
        result = first_num**2
    elif callback.data == "root":
        if first_num < 0:
            await callback.message.answer(
                "Нельзя извлекать корень из отрицательного числа, введите число заново"
            )
            await state.set_state(Logic.need_first)
            return
        result = sqrt(first_num)

    await callback.message.answer(f"Результат операции - {round(result,4)}")
    await state.clear()

    await asyncio.sleep(2)
    await callback.message.answer("Пожалуйста, введите первое число.")
    await state.set_state(Logic.need_first)


@dp.callback_query(
    StateFilter(Logic.need_operation),
    F.data.in_({"add", "subtract", "multiply", "divide"}),
)
async def binary_operation_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(operation=callback.data)
    await state.set_state(Logic.need_second)
    await callback.message.answer("Введите второе число:")


@dp.message(StateFilter(Logic.need_second))
async def second_handler(message: Message, state: FSMContext):
    try:
        value = try_to_get_number(message.text)
    except ValueError:
        await message.answer("Введите число, пожалуйста.")
        return
    data = await state.get_data()
    first_num = float(data["first"])
    operation = data["operation"]
    second_num = float(value)

    if operation == "add":
        result = first_num + second_num
    elif operation == "subtract":
        result = first_num - second_num
    elif operation == "multiply":
        result = first_num * second_num
    elif operation == "divide":
        if second_num == 0:
            await message.answer("Ошибка: на ноль делить нельзя!")
            return
        result = first_num / second_num
    else:
        await message.answer("Неизвестная операция")
        return
    await message.answer(f"Результат операции - {round(result, 4)}")
    await state.clear()
    # data = await state.get_data()
    # print(f"Данные после clear(): {data}")

    await asyncio.sleep(2)
    await message.answer("Пожалуйста, введите первое число.")
    await state.set_state(Logic.need_first)


# Запуск процесса поллинга новых апдейтов
async def main():
    bot = Bot(token=tg_token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

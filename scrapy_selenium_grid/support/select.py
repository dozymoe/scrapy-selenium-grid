# Licensed to the Software Freedom Conservancy (SFC) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The SFC licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from typing import Awaitable
from typing import List
#-
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import UnexpectedTagNameException
from selenium.webdriver.common.by import By
#-
from ..webelement import WebElement

class Select:
    def __init__(self, webelement: WebElement, is_multiple: bool = False) -> None:
        """Constructor. A check is made that the given element is, indeed, a
        SELECT tag. If it is not, then an UnexpectedTagNameException is thrown.

        :Args:
         - webelement - SELECT element to wrap

        Example:
            from selenium.webdriver.support.ui import Select \n
            Select(driver.find_element(By.TAG_NAME, "select")).select_by_index(2)
        """
        if webelement.tag_name.lower() != "select":
            raise UnexpectedTagNameException(
                    "Select only works on <select> elements, not on "
                    f"{webelement.tag_name}")
        self._el = webelement
        self.is_multiple = is_multiple


    @classmethod
    async def create(cls, webelement: WebElement):
        multi = await webelement.get_dom_attribute("multiple")
        return cls(webelement, multi and multi != "false")


    @property
    async def options(self) -> Awaitable[List[WebElement]]:
        """Returns a list of all options belonging to this select tag."""
        return await self._el.find_elements(By.TAG_NAME, "option")


    @property
    async def all_selected_options(self) -> Awaitable[List[WebElement]]:
        """Returns a list of all selected options belonging to this select
        tag."""
        return [opt for opt in await self.options if await opt.is_selected()]


    @property
    async def first_selected_option(self) -> Awaitable[WebElement]:
        """The first selected option in this select tag (or the currently
        selected option in a normal select)"""
        for opt in await self.options:
            if await opt.is_selected():
                return opt
        raise NoSuchElementException("No options are selected")


    async def select_by_value(self, value: str) -> Awaitable[None]:
        """Select all options that have a value matching the argument. That is,
        when given "foo" this would select an option like:

        <option value="foo">Bar</option>

        :Args:
         - value - The value to match against

        throws NoSuchElementException If there is no option with specified value
        in SELECT
        """
        css = f"option[value ={self._escape_string(value)}]"
        opts = await self._el.find_elements(By.CSS_SELECTOR, css)
        matched = False
        for opt in opts:
            await self._set_selected(opt)
            if not self.is_multiple:
                return
            matched = True
        if not matched:
            raise NoSuchElementException(
                    f"Cannot locate option with value: {value}")


    async def select_by_index(self, index: int) -> Awaitable[None]:
        """Select the option at the given index. This is done by examining the
        "index" attribute of an element, and not merely by counting.

        :Args:
         - index - The option at this index will be selected

        throws NoSuchElementException If there is no option with specified index
        in SELECT
        """
        match = str(index)
        for opt in await self.options:
            if await opt.get_attribute("index") == match:
                await self._set_selected(opt)
                return
        raise NoSuchElementException(f"Could not locate element with index {index}")


    async def select_by_visible_text(self, text: str) -> Awaitable[None]:
        """Select all options that display text matching the argument. That is,
        when given "Bar" this would select an option like:

         <option value="foo">Bar</option>

        :Args:
         - text - The visible text to match against

        throws NoSuchElementException If there is no option with specified text
        in SELECT
        """
        xpath = f".//option[normalize-space(.) = {self._escape_string(text)}]"
        opts = await self._el.find_elements(By.XPATH, xpath)
        matched = False
        for opt in opts:
            await self._set_selected(opt)
            if not self.is_multiple:
                return
            matched = True

        if len(opts) == 0 and " " in text:
            sub_string_without_space = self._get_longest_token(text)
            if sub_string_without_space == "":
                candidates = await self.options
            else:
                xpath = (
                    ".//option[contains(.,"
                    f"{self._escape_string(sub_string_without_space)})]"
                )
                candidates = await self._el.find_elements(By.XPATH, xpath)
            for candidate in candidates:
                if text == await candidate.text:
                    await self._set_selected(candidate)
                    if not self.is_multiple:
                        return
                    matched = True

        if not matched:
            raise NoSuchElementException(
                    f"Could not locate element with visible text: {text}")


    async def deselect_all(self) -> Awaitable[None]:
        """Clear all selected entries.

        This is only valid when the SELECT supports multiple selections.
        throws NotImplementedError If the SELECT does not support
        multiple selections
        """
        if not self.is_multiple:
            raise NotImplementedError(
                    "You may only deselect all options of a multi-select")
        for opt in await self.options:
            await self._unset_selected(opt)


    async def deselect_by_value(self, value: str) -> Awaitable[None]:
        """Deselect all options that have a value matching the argument. That
        is, when given "foo" this would deselect an option like:

         <option value="foo">Bar</option>

        :Args:
         - value - The value to match against

        throws NoSuchElementException If there is no option with specified value
        in SELECT
        """
        if not self.is_multiple:
            raise NotImplementedError(
                    "You may only deselect options of a multi-select")
        matched = False
        css = f"option[value = {self._escape_string(value)}]"
        opts = await self._el.find_elements(By.CSS_SELECTOR, css)
        for opt in opts:
            await self._unset_selected(opt)
            matched = True
        if not matched:
            raise NoSuchElementException(
                    f"Could not locate element with value: {value}")


    async def deselect_by_index(self, index: int) -> Awaitable[None]:
        """Deselect the option at the given index. This is done by examining
        the "index" attribute of an element, and not merely by counting.

        :Args:
         - index - The option at this index will be deselected

         throws NoSuchElementException If there is no option with specified index in SELECT
        """
        if not self.is_multiple:
            raise NotImplementedError(
                    "You may only deselect options of a multi-select")
        for opt in await self.options:
            if await opt.get_attribute("index") == str(index):
                await self._unset_selected(opt)
                return
        raise NoSuchElementException(
                f"Could not locate element with index {index}")


    async def deselect_by_visible_text(self, text: str) -> Awaitable[None]:
        """Deselect all options that display text matching the argument. That
        is, when given "Bar" this would deselect an option like:

        <option value="foo">Bar</option>

        :Args:
         - text - The visible text to match against
        """
        if not self.is_multiple:
            raise NotImplementedError(
                    "You may only deselect options of a multi-select")
        matched = False
        xpath = f".//option[normalize-space(.) = {self._escape_string(text)}]"
        opts = await self._el.find_elements(By.XPATH, xpath)
        for opt in opts:
            await self._unset_selected(opt)
            matched = True
        if not matched:
            raise NoSuchElementException(
                    f"Could not locate element with visible text: {text}")


    async def _set_selected(self, option) -> Awaitable[None]:
        if not await option.is_selected():
            if not await option.is_enabled():
                raise NotImplementedError("You may not select a disabled option")
            await option.click()


    async def _unset_selected(self, option) -> Awaitable[None]:
        if await option.is_selected():
            await option.click()


    def _escape_string(self, value: str) -> str:
        if '"' in value and "'" in value:
            substrings = value.split('"')
            result = ["concat("]
            for substring in substrings:
                result.append(f'"{substring}"')
                result.append(", '\"', ")
            result = result[0:-1]
            if value.endswith('"'):
                result.append(", '\"'")
            return "".join(result) + ")"

        if '"' in value:
            return f"'{value}'"

        return f'"{value}"'


    def _get_longest_token(self, value: str) -> str:
        items = value.split(" ")
        longest = ""
        for item in items:
            if len(item) > len(longest):
                longest = item
        return longest

from pydantic import BaseModel, Field, EmailStr
from typing import Optional

# Customers
class CreateCustomerIn(BaseModel):
    fullName: str = Field(..., min_length=1)
    email: EmailStr                                                    # EmailStr is import from pydantic.
    phoneNumber: Optional[str] = Field(default=None, max_length=15)  # field is to specific validation

class GetCustomerIn(BaseModel):
    id: int = Field(..., ge=1)

class ListCustomerTxIn(BaseModel):
    id: int = Field(..., ge=1)  # customer id , three dots mean that the field is required
    status: Optional[str] = None
    category: Optional[str] = None  # means the default value is None
    currency: Optional[str] = None
    from_: Optional[str] = Field(default=None, alias="from")  # field is used to specify validation in addition to default values
    to: Optional[str] = None
    page: int = 0
    size: int = 10
    sort: str = "createdAt,desc"

# Transactions
class CreateTransactionIn(BaseModel):
    customerId: int = Field(..., ge=1)
    amount: float = Field(..., ge=0)
    currency: str
    category: str
    description: Optional[str] = None
    idempotencyKey: Optional[str] = None

class GetTransactionIn(BaseModel):
    id: int = Field(..., ge=1)

class SearchTransactionsIn(BaseModel):
    customerId: Optional[int] = None
    status: Optional[str] = None
    category: Optional[str] = None
    currency: Optional[str] = None
    from_: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = None
    page: int = 0
    size: int = 10
    sort: str = "createdAt,desc"

class CancelTransactionIn(BaseModel):
    id: int = Field(..., ge=1)
    idempotencyKey: Optional[str] = None

# Payments
class MakePaymentIn(BaseModel):
    transactionId: int = Field(..., ge=1)
    method: str
    idempotencyKey: Optional[str] = None

class GetPaymentIn(BaseModel):
    id: int = Field(..., ge=1)

class GetPaymentByTxIn(BaseModel):
    transactionId: int = Field(..., ge=1)

class RetryPaymentIn(BaseModel):
    id: int = Field(..., ge=1)
    idempotencyKey: Optional[str] = None

class FailPaymentIn(BaseModel):
    id: int = Field(..., ge=1)
    reasonCode: str
    idempotencyKey: Optional[str] = None

# Analytics
class SpendSummaryIn(BaseModel):
    customerId: int = Field(..., ge=1)
    from_: str = Field(..., alias="from")
    to: str
    fxBase: str = "USD"

class SpendByCategoryIn(BaseModel):
    customerId: int = Field(..., ge=1)
    from_: str = Field(..., alias="from")
    to: str

class TimeSeriesIn(BaseModel):
    customerId: int = Field(..., ge=1)
    bucket: str  # day|week|month
    from_: str = Field(..., alias="from")
    to: str
    category: Optional[str] = None

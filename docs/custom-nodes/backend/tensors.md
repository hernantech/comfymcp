# Working with torch.Tensor

## pytorch, tensors, and torch.Tensor

Core number crunching in Comfy uses PyTorch. Custom nodes working with images, latents, and masks need familiarity with `torch.Tensor` representations.

## What is a Tensor?

A tensor generalizes vectors and matrices to any number of dimensions. Its rank indicates the number of dimensions; shape describes each dimension's size. Comfy images follow the pattern `[B,H,W,C]` where B is batch size, H and W are spatial dimensions, and C represents color channels (typically 3 for RGB).

## squeeze, unsqueeze, and reshape

Removing such a collapsed dimension is referred to as squeezing, and inserting one is known as unsqueezing. Reshaping represents data in different shapes but requires understanding the underlying data structure.

> **Warning**: Some torch code will return a squeezed tensor when a dimension is collapsed—such as when a batch has only one member. This is a common cause of bugs!

## Important notation

Key notation includes:

- Using `None` in slice notation inserts a dimension of size 1
- `:` means "keep the whole dimension"
- `...` represents "the whole of an unspecified number of dimensions"
- `-1` in shape specifications means "calculate this dimension based on total data size"

### Example - Tensor shape and slicing

```python
>>> a = torch.Tensor((1,2))
>>> a.shape
torch.Size([2])
>>> a[:,None].shape
torch.Size([2, 1])
>>> a.reshape((1,-1)).shape
torch.Size([1, 2])
```

## Elementwise operations

Binary operations on tensors (`+`, `-`, `*`, `/`, `==`) apply independently to each element. Operands must be either identical-shaped tensors or a tensor with a scalar.

### Example - Elementwise operations

```python
>>> import torch
>>> a = torch.Tensor((1,2))
>>> b = torch.Tensor((3,2))
>>> a*b
tensor([3., 4.])
>>> a/b
tensor([0.3333, 1.0000])
>>> a==b
tensor([False,  True])
>>> a==1
tensor([ True, False])
>>> c = torch.Tensor((3,2,1))
>>> a==c
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
RuntimeError: The size of tensor a (2) must match the size of tensor b (3) at non-singleton dimension 0
```

## Tensor truthiness

A `torch.Tensor` (with more than one element) does not have a defined truthy value. Use `.all()` or `.any()` for boolean evaluation, and `if a is not None:` rather than `if a:` to check tensor assignment.

### Example - Tensor truthiness

```python
>>> a = torch.Tensor((1,2))
>>> print("yes" if a else "no")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
RuntimeError: Boolean value of Tensor with more than one value is ambiguous
>>> a.all()
tensor(False)
>>> a.any()
tensor(True)
```

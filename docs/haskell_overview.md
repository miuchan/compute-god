# Haskell 全景实践指南

本指南整理了 Haskell 语言核心理念与子概念，提供概念讲解、示例代码以及实践建议，帮助你快速串联纯函数式编程体系。所有示例均可直接在 `ghci` 中运行或保存为 `.hs` 文件进行编译。

## 语言定位与设计哲学

- **纯函数式**：程序由表达式组成，强调可推导性与无副作用。
- **非严格（惰性求值）**：按需计算，支持无限结构与延迟求值。
- **强静态类型**：借助类型系统提前捕获错误，编译器自动推导大部分类型。

## 纯函数式编程

```haskell
square :: Num a => a -> a
square x = x * x
```

- 函数是“一等公民”，可作为参数或返回值。
- 数据不可变，所有“修改”通过返回新值实现。
- 纯函数保证相同输入必得相同输出，便于测试与重构。

## 惰性求值

```haskell
naturals :: [Integer]
naturals = [0..]

firstTen :: [Integer]
firstTen = take 10 naturals
```

- 列表 `naturals` 在未消费前不会真正生成，`take` 只取需要的前 10 个。
- 如需控制内存，可使用严格版本的折叠 `foldl'` 或 `seq`。

## 类型系统基础

### 代数数据类型（ADTs）

```haskell
data Shape
  = Circle Double
  | Rectangle Double Double
  deriving (Show)
```

- `Circle`、`Rectangle` 是构造子，描述不同形态。
- 利用模式匹配处理不同分支：

```haskell
area :: Shape -> Double
area (Circle r)        = pi * r ^ 2
area (Rectangle w h) = w * h
```

### 记录语法

```haskell
data User = User
  { name :: String
  , age  :: Int
  } deriving (Show)
```

- 通过 `name user`、`age user` 访问字段。

### `type` 与 `newtype`

```haskell
type UserId = Int

newtype Email = Email String
  deriving (Show, Eq)
```

- `type` 仅是别名；`newtype` 创建与原类型等价的零开销新类型。

### 参数多态与高阶类型

```haskell
safeHead :: [a] -> Maybe a
safeHead []    = Nothing
safeHead (x:_) = Just x
```

- 使用类型变量 `a` 表示“对所有类型适用”。

## 类型类

```haskell
class Describable a where
  describe :: a -> String

instance Describable Shape where
  describe (Circle r) = "Circle radius=" ++ show r
  describe (Rectangle w h) = "Rectangle " ++ show w ++ "×" ++ show h
```

- 类型类定义行为契约，实例提供具体实现。
- Haskell 标准库常见类型类：`Eq`、`Ord`、`Show`、`Enum`、`Functor`、`Applicative`、`Monad` 等。

## Monoid / Functor / Applicative / Monad

```haskell
import Data.Monoid (Sum(..))

-- Monoid：定义幺元与结合操作
mconcatExample :: Sum Int
mconcatExample = mconcat [Sum 1, Sum 2, Sum 3]  -- 结果 Sum {getSum = 6}

-- Functor：在上下文中映射函数
maybeInc :: Maybe Int
maybeInc = fmap (+1) (Just 3)  -- Just 4

-- Applicative：组合上下文中的函数与值
applyExample :: Maybe Int
applyExample = pure (+) <*> Just 2 <*> Just 3  -- Just 5

-- Monad：串联带上下文的计算
maybeBind :: Maybe Int
maybeBind = Just 3 >>= (\x -> if x > 0 then Just (x * 2) else Nothing)
```

## 模块与依赖管理

- **模块声明**：`module Geometry (area) where` 控制导出符号。
- **构建工具**：`stack new my-project` 或 `cabal init` 初始化项目。
- **常用库**：`text`、`bytestring`、`containers`、`aeson`、`lens` 等。

## 副作用建模

```haskell
main :: IO ()
main = do
  putStrLn "What is your name?"
  userName <- getLine
  putStrLn ("Hello, " ++ userName ++ "!")
```

- `IO` Monad 将副作用封装在类型中。
- `do` 记号是语法糖，等价于多次 `>>=`。

### `ST` Monad 示例

```haskell
import Control.Monad.ST
import Data.STRef

sumST :: [Int] -> Int
sumST xs = runST $ do
  acc <- newSTRef 0
  mapM_ (modifySTRef' acc . (+)) xs
  readSTRef acc
```

## 控制结构

- **模式匹配**：区分构造子，保证穷尽性检查。
- **守卫与 where**：

```haskell
bmiTell :: RealFloat a => a -> String
bmiTell bmi
  | bmi <= 18.5 = "Underweight"
  | bmi <= 25.0 = "Normal"
  | bmi <= 30.0 = "Overweight"
  | otherwise   = "Obese"
```

- **列表推导**：`[x * 2 | x <- [1..10], even x]`。

## 高级类型与扩展

- **GADTs**：

```haskell
{-# LANGUAGE GADTs #-}

data Expr a where
  LitInt  :: Int  -> Expr Int
  LitBool :: Bool -> Expr Bool
  Add     :: Expr Int -> Expr Int -> Expr Int
```

- **Type Families**、**Multi-Parameter Type Classes**：扩展类型层级编程能力。
- **DataKinds** 与 **TypeInType**：将值提升到类型层面，实现精细约束。

## 并发与并行

```haskell
import Control.Concurrent

printAsync :: IO ()
printAsync = do
  forkIO $ putStrLn "Running in another thread"
  threadDelay 1000
  putStrLn "Main thread done"
```

- 使用 `STM` 提供事务内存：

```haskell
import Control.Concurrent.STM

transfer :: Int -> TVar Int -> TVar Int -> IO ()
transfer amount from to = atomically $ do
  balance <- readTVar from
  if balance >= amount
     then writeTVar from (balance - amount) >> modifyTVar' to (+ amount)
     else retry
```

## 工具链与调试

- **GHCi**：`ghci` 进入交互环境，使用 `:load`, `:type`, `:info` 探索代码。
- **Profiling**：编译时添加 `-prof -fprof-auto`，运行时使用 `+RTS -p`。
- **格式化与静态检查**：`fourmolu`、`hlint` 提供代码风格与重构建议。

## 学习资源与实践路径

1. 阅读《Learn You a Haskell for Great Good!》《Programming in Haskell》建立基础。
2. 在 `exercism.io`、`Codewars` 完成渐进练习巩固语法与抽象。
3. 实践项目：命令行工具、Servant/Yesod Web 服务、数据流水线。
4. 关注社区：Haskell Weekly、/r/haskell、Stack Overflow。

---

通过按图索骥掌握上述概念，你可以逐步搭建对 Haskell 语言的系统认知，在纯函数式范式中构建安全、优雅且可拓展的软件。

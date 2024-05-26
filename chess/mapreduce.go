package chess

func Filter(f func(any) any, inch chan any) chan any {
	ouch := make(chan any)
	go func() {
		defer close(ouch)
		for input := range inch {
			output := f(input)
			if output.(bool) {
				ouch <- input
			}
		}
	}()
	return ouch
}

func Map(f func(any) any, inch chan any) chan any {
	ouch := make(chan any)
	go func() {
		defer close(ouch)
		for input := range inch {
			output := f(input)
			ouch <- output
		}
	}()
	return ouch
}

func Reduce(f func(x, y any) any, inch chan any, initial any) any {
	accumulator := initial
	for k := range inch {
		accumulator = f(accumulator, k)
	}
	return accumulator
}

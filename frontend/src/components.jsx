function Block({ children, ...props }) {
    return (
        <div {...props}>
            {children}
        </div>
    )
}

export { Block }
# Contributing to KUYAN

Thank you for considering contributing to KUYAN! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment for all contributors

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)

### Suggesting Features

Feature suggestions are welcome! Please:
- Check if the feature already exists or is planned
- Describe the use case clearly
- Explain why it would benefit KUYAN users

### Submitting Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Add comments for complex logic
   - Keep commits focused and atomic

4. **Test your changes**
   - Test in both production and sandbox mode
   - Verify Docker deployment works
   - Check that existing features still work

5. **Commit your changes**
   ```bash
   git commit -m "Add feature: description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Describe what your PR does
   - Reference any related issues
   - Include screenshots if UI changes

## Development Setup

### Local Development

```bash
# Clone the repository
git clone https://github.com/dc-shimla/kuyan.git
cd kuyan

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### Testing with Docker

```bash
# Build and run
./scripts/docker-build.sh
./scripts/docker-start.sh

# Access sandbox mode
# http://localhost:8501/?mode=sandbox
```

## Code Style Guidelines

- **Python**: Follow PEP 8 style guide
- **Comments**: Use clear, concise comments
- **Naming**: Use descriptive variable and function names
- **Imports**: Group stdlib, third-party, and local imports

## Areas for Contribution

Here are some areas where contributions are especially welcome:

### High Priority
- Bug fixes and stability improvements
- Documentation improvements
- UI/UX enhancements
- Performance optimizations

### Feature Ideas
- Additional currency support
- CSV/Excel export functionality
- Data visualization improvements
- Multi-language support (i18n)
- Mobile-responsive improvements
- Backup automation features

### Advanced Features
- Encryption for database files
- Investment tracking (stocks, crypto)
- Budget tracking integration
- Goal setting and progress tracking

## Security Considerations

KUYAN handles sensitive financial data. When contributing:

- **Never** commit sensitive data (database files, credentials)
- Be cautious with external dependencies
- Consider privacy implications of new features
- Report security issues privately (create a GitHub security advisory)

## Testing Checklist

Before submitting a PR, verify:

- [ ] Code runs without errors
- [ ] Existing features still work
- [ ] Database operations don't corrupt data
- [ ] UI renders correctly in both light/dark themes
- [ ] Docker deployment works
- [ ] Sandbox mode works correctly
- [ ] No sensitive data in commits

## Questions?

If you have questions about contributing:
- Open an issue with the "question" label
- Check existing issues and discussions
- Review the README documentation

## License

By contributing to KUYAN, you agree that your contributions will be licensed under the MIT License.

---

Thank you for helping make KUYAN better! 🙏

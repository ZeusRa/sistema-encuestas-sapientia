import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import React from 'react';

const Simple = () => <div>Hello World</div>;

describe('Simple Component', () => {
    it('renders', () => {
        render(<Simple />);
        expect(screen.getByText('Hello World')).toBeInTheDocument();
    });
});

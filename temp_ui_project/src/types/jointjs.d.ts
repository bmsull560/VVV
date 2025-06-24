declare module '@joint/core' {
  namespace dia {
    interface Element {
      componentId?: string;
      componentType?: string;
    }

    interface Paper {
      drawGrid(options: { name: string; args?: unknown }): void;
      scaleContentToFit(options?: { padding?: number }): void;
      zoomToFit(options?: { padding?: number }): void;
    }
  }
}

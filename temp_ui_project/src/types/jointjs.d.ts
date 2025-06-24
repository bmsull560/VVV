declare namespace Backbone {
  class Events {
    on(eventName: string, callback?: (...args: unknown[]) => void, context?: unknown): void;
    off(eventName?: string, callback?: (...args: unknown[]) => void, context?: unknown): void;
    trigger(eventName: string, ...args: unknown[]): void;
  }

  class Model extends Events {
    id?: string;
    get(attribute: string): unknown;
    set(attribute: string, value: unknown, options?: unknown): void;
    toJSON(): object;
  }

  class View<T extends Model> extends Events {
    model?: T;
    el: HTMLElement;
    $: JQuery;
    constructor(options?: unknown);
    remove(): this;
    setElement(element: HTMLElement | JQuery, delegate?: boolean): this;
    delegateEvents(events?: unknown): this;
    undelegateEvents(): this;
  }
}

declare module '@joint/core' {
  namespace dia {
    interface Graph extends Backbone.Events {
      addCell(cell: Cell | Cell[]): this;
      removeCells(cells: Cell[]): this;
      getCell(id: string): Cell | undefined;
      getCells(): Cell[];
      getElements(): Element[];
      getLinks(): Link[];
      clear(): this;
    }

    interface Cell extends Backbone.Model {
      get(property: string): unknown;
      set(property: string, value: unknown): this;
      isLink(): boolean;
      isElement(): boolean;
    }

    interface Element extends Cell {
      componentId?: string;
      componentType?: string;
      position(): { x: number; y: number };
      size(): { width: number; height: number };
    }

    interface Link extends Cell {
      getSourceElement(): Element | undefined;
      getTargetElement(): Element | undefined;
    }

    interface CellView extends Backbone.View<Cell> {
      model: Cell;
      paper: Paper;
    }

    interface ElementView extends CellView {
      model: Element;
    }

    interface LinkView extends CellView {
      model: Link;
    }

    interface Paper {
      drawGrid(options: { name: string; args?: unknown }): void;
      scaleContentToFit(options?: { padding?: number }): void;
      zoomToFit(options?: { padding?: number }): void;
      scale(sx: number, sy: number): void;
      on(eventName: string, handler: (...args: unknown[]) => void): void;
      off(eventName: string): void;
    }
  }
}
